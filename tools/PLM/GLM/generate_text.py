# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample Generate GPT2 to be called"""

import os, sys

import torch
import torch.nn.functional as F
from pathlib import Path,PurePath
from datetime import datetime
import time
import json
import sys
BASE_DIR = Path(__file__).parent
sys.path.append(BASE_DIR)
from generate_samples import get_batch,top_k_logits,BeamSearchScorer,mpu
from dataclasses import dataclass
from typing import Any


class Config:
	def __init__(self, entries: dict={}):
		self.__dict__.update(entries)

def get_args(gpu=0):
    """Parse all the args."""
    path = Path(__file__).parent
    filepath = PurePath(path).joinpath("glm_config.json")
    with open(filepath, 'r') as f:
        args_dict = json.load(f)
    args = Config(args_dict)
    args.gpu = str(gpu)

    if not args.train_data and not args.data_dir:
        print('WARNING: No training data specified')

    args.cuda = torch.cuda.is_available()

    args.rank = int(os.getenv('RANK', '0'))
    args.world_size = int(os.getenv("WORLD_SIZE", '1'))
    if os.getenv('OMPI_COMM_WORLD_LOCAL_RANK'):
        # We are using (OpenMPI) mpirun for launching distributed data parallel processes
        local_rank = int(os.getenv('OMPI_COMM_WORLD_LOCAL_RANK'))
        local_size = int(os.getenv('OMPI_COMM_WORLD_LOCAL_SIZE'))

        # Possibly running with Slurm
        num_nodes = int(os.getenv('SLURM_JOB_NUM_NODES', '1'))
        nodeid = int(os.getenv('SLURM_NODEID', '0'))

        args.local_rank = local_rank
        args.rank = nodeid * local_size + local_rank
        args.world_size = num_nodes * local_size

    args.model_parallel_size = min(args.model_parallel_size, args.world_size)
    if args.rank == 0:
        print('using world size: {} and model-parallel size: {} '.format(
            args.world_size, args.model_parallel_size))

    args.dynamic_loss_scale = False
    if args.loss_scale is None:
        args.dynamic_loss_scale = True
        if args.rank == 0:
            print(' > using dynamic loss scaling')

    # The args fp32_* or fp16_* meant to be active when the
    # args fp16 is set. So the default behaviour should all
    # be false.
    if not args.fp16:
        args.fp32_embedding = False
        args.fp32_tokentypes = False
        args.fp32_layernorm = False

    if hasattr(args, "deepspeed") and args.deepspeed and args.deepspeed_config is not None:
        with open(args.deepspeed_config) as file:
            deepspeed_config = json.load(file)
        if "train_micro_batch_size_per_gpu" in deepspeed_config:
            args.batch_size = deepspeed_config["train_micro_batch_size_per_gpu"]
        if "gradient_accumulation_steps" in deepspeed_config:
            args.gradient_accumulation_steps = deepspeed_config["gradient_accumulation_steps"]
        else:
            args.gradient_accumulation_steps = 1
        if "optimizer" in deepspeed_config:
            optimizer_params_config = deepspeed_config["optimizer"].get("params", {})
            args.lr = optimizer_params_config.get("lr", args.lr)
            args.weight_decay = optimizer_params_config.get("weight_decay", args.weight_decay)
    return args

#param = Parameter()

def sample_sequence(model, tokenizer, context_tokens, context_length, args, device, mems=None, end_tokens=None):
    if not args.block_lm:
        context_tokens, attention_mask, position_ids = get_batch(context_tokens, device, args)
        tokens = torch.empty((args.num_beams, 0), device=context_tokens.device, dtype=torch.long)
    else:
        tokens = context_tokens.new_full((1, 1), tokenizer.get_command('sop').Id)
    counter = 0
    if mems is None:
        mems = []
    if end_tokens is None:
        end_tokens = [args.eod_token]
    if args.num_beams > 1:
        beam_scorer = BeamSearchScorer(
            batch_size=1,
            max_length=args.out_seq_length,
            num_beams=args.num_beams,
            device=context_tokens.device,
            length_penalty=args.length_penalty,
            do_early_stopping=False,
        )
        beam_scores = torch.zeros(1, dtype=torch.float, device=context_tokens.device)
    last_beam_num = 1
    while counter < args.out_seq_length:
        if counter == 0 and not args.block_lm:
            next_token_logits, *mems = model(context_tokens, position_ids, attention_mask, *mems)
        else:
            if args.block_lm:
                if args.no_block_position:
                    position_ids = context_tokens.new_full((last_beam_num, 1), context_length + counter)
                else:
                    position_ids = context_tokens.new_ones(last_beam_num, 2, 1)
                    position_ids[:, 0] = context_length
                    position_ids[:, 1] = counter + 1
                attention_mask = context_tokens.new_zeros([1], device=context_tokens.device, dtype=torch.long)
            else:
                position_ids = context_tokens.new_ones((last_beam_num, 1)) * (context_length + counter - 1)
                attention_mask = context_tokens.new_ones(last_beam_num, 1, 1, args.mem_length + 1,
                                                         device=context_tokens.device, dtype=torch.float)
            last_token = tokens[:, -1:]
            next_token_logits, *mems = model(last_token, position_ids, attention_mask, *mems)
        next_token_logits = next_token_logits[:, -1]
        if args.num_beams > 1:
            next_token_scores = F.log_softmax(next_token_logits, dim=-1)
            next_token_scores = next_token_scores + beam_scores[:, None].expand_as(next_token_scores)
            vocab_size = next_token_scores.shape[-1]
            next_token_scores = next_token_scores.view(1, last_beam_num * vocab_size)

            probs = F.softmax(next_token_scores, dim=-1)
            next_tokens = torch.multinomial(probs, num_samples=2 * args.num_beams)
            next_token_scores = torch.gather(next_token_scores, -1, next_tokens)
            next_token_scores, _indices = torch.sort(next_token_scores, descending=True, dim=1)
            next_tokens = torch.gather(next_tokens, -1, _indices)

            next_indices = next_tokens // vocab_size
            next_tokens = next_tokens % vocab_size
            # stateless
            tokens = tokens.expand((args.num_beams, -1))
            beam_outputs = beam_scorer.process(
                tokens,
                next_token_scores,
                next_tokens,
                next_indices,
                eos_token_id=end_tokens,
                mems=mems
            )
            beam_scores = beam_outputs["next_beam_scores"]
            beam_next_tokens = beam_outputs["next_beam_tokens"]
            beam_idx = beam_outputs["next_beam_indices"]
            beam_next_tokens = beam_next_tokens.unsqueeze(-1)
            tokens = torch.cat([tokens[beam_idx, :], beam_next_tokens], dim=-1)
            mems = [mem[beam_idx] for mem in mems] if mems else None
            if beam_scorer.is_done:
                break
            last_beam_num = args.num_beams
        else:
            next_token_logits /= args.temperature
            next_token_logits = top_k_logits(next_token_logits, top_k=args.top_k, top_p=args.top_p)
            log_probs = F.softmax(next_token_logits, dim=-1)
            prev = torch.multinomial(log_probs, num_samples=1)[0]
            is_end = prev.item() in end_tokens
            if is_end:
                break
            prev = prev.view(1, 1)
            tokens = prev if tokens is None else torch.cat((tokens, prev), dim=1)
        counter += 1
        if not args.block_lm and mpu.get_model_parallel_rank() == 0 and counter % 16 == 0:
            output_tokens_list = tokens.view(-1).contiguous()
            decode_tokens = tokenizer.DecodeIds(output_tokens_list.tolist())
            if mpu.get_model_parallel_rank() == 0 and (counter % 128 == 0 or is_end):
                #os.system('clear')
                trim_decode_tokens = decode_tokens
                print(trim_decode_tokens, flush=True)
    if args.num_beams > 1:
        tokens, mems = beam_scorer.finalize(tokens, beam_scores, next_tokens, next_indices, eos_token_id=args.eod_token,
                                            mems=mems)
    return torch.cat((context_tokens, tokens), dim=1), mems


def generate_samples(raw_text, model, tokenizer, args, device):
    model.eval()
    start_time = time.time()

    with torch.no_grad():
        torch.distributed.barrier(group=mpu.get_model_parallel_group())
        context_tokens = tokenizer.EncodeAsIds(raw_text).tokenization
        eo_tokens = tokenizer.EncodeAsIds("<|endoftext|>").tokenization
        context_length = len(context_tokens)
        if context_length >= args.seq_length:
            context_tokens = context_tokens[-(args.seq_length - 1) :]
            context_length = len(context_tokens)
            raw_text = tokenizer.DecodeIds(context_tokens)

        context_tokens_tensor = torch.cuda.LongTensor(context_tokens)
        eo_token_tensor = torch.cuda.LongTensor(eo_tokens)
        context_length_tensor = torch.cuda.LongTensor([context_length])

        output_tokens_list, _ = sample_sequence(
            model, tokenizer, context_tokens_tensor, context_length, args, device
        )
        if mpu.get_model_parallel_rank() == 0:
            # os.system('clear')
            print("\nTaken time {:.2f}\n".format(time.time() - start_time), flush=True)
            print("\nContext:", raw_text, flush=True)
            decode_tokens = tokenizer.DecodeIds(output_tokens_list.tolist())
            trim_decode_tokens = decode_tokens[len(raw_text) :]
            print("\nGPT2:", trim_decode_tokens, flush=True)
            print("decode_tokens:", decode_tokens)

        torch.distributed.barrier(group=mpu.get_model_parallel_group())
    return trim_decode_tokens


def get_prepared(gpu=0):
    print("Get prepared for GLM generation module")

    # Disable CuDNN.
    torch.backends.cudnn.enabled = False
    from generate_samples import initialize_distributed,set_random_seed,prepare_tokenizer,setup_model,generate_samples
    # Arguments.
    args = get_args()
    args.mem_length = args.seq_length + args.mem_length - 1

    # Pytorch distributed.
    initialize_distributed(args)

    # Random seeds for reproducability.
    set_random_seed(args.seed)

    # get the tokenizer
    tokenizer = prepare_tokenizer(args)

    # Model, optimizer, and learning rate.
    model = setup_model(args)

    # setting default batch size to 1
    args.batch_size = 1
    return model, tokenizer, args

def generate_samples(raw_text, model, tokenizer, args, device):
    model.eval()
    start_time = time.time()

    with torch.no_grad():
        torch.distributed.barrier(group=mpu.get_model_parallel_group())
        generation_mask = '[gMASK]' if args.task_mask else '[MASK]'
        if args.block_lm and 'MASK]' not in raw_text:
            raw_text += ' ' + generation_mask

        context_tokens = tokenizer.EncodeAsIds(raw_text).tokenization
        if args.block_lm:
            context_tokens = [tokenizer.get_command('ENC').Id] + context_tokens
            if not raw_text.endswith('MASK]'):
                context_tokens = context_tokens + [tokenizer.get_command('eos').Id]
        context_length = len(context_tokens)
        if context_length >= args.seq_length:
            print("\nContext length", context_length,
                  "\nPlease give smaller context than the window length!")


        context_length_tensor = torch.cuda.LongTensor([context_length])

        torch.distributed.broadcast(context_length_tensor, mpu.get_model_parallel_src_rank(),
                                    group=mpu.get_model_parallel_group())
        context_length = context_length_tensor[0].item()
        if mpu.get_model_parallel_rank() == 0:
            context_tokens_tensor = torch.cuda.LongTensor(context_tokens)
        else:
            context_tokens_tensor = torch.cuda.LongTensor([0] * context_length)
        torch.distributed.broadcast(context_tokens_tensor, mpu.get_model_parallel_src_rank(),
                                    group=mpu.get_model_parallel_group())
        if mpu.get_model_parallel_rank() != 0:
            raw_text = tokenizer.DecodeIds(context_tokens_tensor.tolist())

        if args.block_lm:
            mems = []
            tokens, attention_mask, position_ids = get_batch(context_tokens_tensor, device, args)
            mask_tokens = ['MASK', 'sMASK', 'gMASK'] if args.task_mask else ['MASK']
            mask_tokens = [tokenizer.get_command(token).Id for token in mask_tokens]
            end_tokens = [tokenizer.get_command('eop').Id, args.eod_token]
            mask_positions = []
            for token in mask_tokens:
                mask_positions += (context_tokens_tensor == token).nonzero(as_tuple=True)[0].tolist()
            mask_positions.sort()
            if args.no_block_position:
                for mask_position in mask_positions:
                    position_ids[0, mask_position + 1:] += args.out_seq_length
            _, *mems = model(tokens, position_ids, attention_mask, *mems)
            for mask_position in mask_positions:
                if args.no_block_position:
                    position = position_ids[0, mask_position].item()
                else:
                    position = mask_position
                tokens, mems = sample_sequence(model, tokenizer, tokens, position,
                                               args, device, mems=mems, end_tokens=end_tokens)
        else:
            tokens, _ = sample_sequence(model, tokenizer, context_tokens_tensor, context_length, args, device)
        output_tokens_list = tokens.view(-1).contiguous()
        if mpu.get_model_parallel_rank() == 0:
            print("\nTaken time {:.2f}\n".format(time.time() - start_time), flush=True)
            print("\nContext:", raw_text, flush=True)
            decode_tokens = tokenizer.DecodeIds(output_tokens_list.tolist())
            trim_decode_tokens = decode_tokens
            print("\nGLM:", trim_decode_tokens, flush=True)
        torch.distributed.barrier(group=mpu.get_model_parallel_group())
    return trim_decode_tokens


if __name__ == "__main__":
    model, tokenizer, args = get_prepared()
    args.out_seq_length = 30
    text = '你好,我是一名大三学生,我即将面临毕业,毕业以后将面临就业的问题,但是我现在就业压力很大,我不知道该怎么办? 你可能不知道'
    generate_samples(text, model, tokenizer, args, torch.cuda.current_device())

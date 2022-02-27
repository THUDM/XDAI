from pyhanlp import HanLP
import thulac
import jieba
import jieba.posseg as pseg
import re
from .stopwords import stopwordslist

class PosTagging:
    thucut = thulac.thulac(seg_only=False, filt=True)
    thucut_seg_only = thulac.thulac(seg_only=True, deli='_')
    stopw = stopwordslist()

    @classmethod
    def segs(cls,string,method="hanlp",seg_only=True,segdict=False):
        if method =="hanlp":
            tmp = HanLP.segment(string)
            seg = [(t.word, str(t.nature)) for t in tmp]
        elif method =="thulac":
            seg = cls.thucut.cut(string)
        elif method == "jieba":
            seg = pseg.cut(string,use_paddle=True)
            seg = [(word,flag) for word,flag in seg]

        segdict = {i[0]: i[1] for i in seg}

        if seg_only == True:
            seg = [i[0] for i in seg]

        if segdict:
            return seg, segdict
        else:
            return seg

    @staticmethod
    def check_pos(flag,method="hanlp",special=True):
        if method == "hanlp":
            if special:
                pattern = re.compile(r"(n[^inxz]+)|(g.*)$")
            else:
                pattern = re.compile(r"v?(n.+)|(g.*)$")
        if re.match(pattern, flag) is not None:
            return True
        else:
            return False



if __name__ =="__main__":
    text ="""
    人民网华盛顿3月28日电（记者郑琪）据美国约翰斯·霍普金斯大学疫情实时监测系统显示，截至美东时间3月28日下午6时，
美国已经至少有新冠病毒感染病例121117例，其中包括死亡病例2010例。
与大约24小时前相比，美国确诊病例至少增加了20400例，死亡病例至少增加了466例。
目前美国疫情最为严重的仍是纽约州，共有确诊病例至少52410例。此外，新泽西州有确诊病例11124例，加利福尼亚州有5065例，
密歇根州有4650例，马塞诸塞州有4257例，华盛顿州有4008例。
"""
    for method in ["jieba","hanlp","thulac"]:
        seg = PosTagging.segs(text, method=method)
        print(seg)
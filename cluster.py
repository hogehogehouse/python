#! /usr/bin/python
# coding: utf-8

import MeCab, sys
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import Normalizer

NUM_CLUSTERS = 5 # 分割するクラスタ数
LSA_DIM = 500 # 
MAX_DF = 0.8 # DF>=0.8以上は除外
MAX_FEATURES = 10000 # 考慮する単語の最大数
MINIBATCH = True

# 改行区切りのファイルからレコードを読み込み
def get_bio_from_txt(filename):
    return open(filename, 'r').readlines()

# textを形態素解析にかけて、名詞のリストを返す関数
def analyzer(text):
    ret = []
    tagger = MeCab.Tagger()
    node = tagger.parseToNode(text)
    node = node.next
    while node.next:
        if node.feature.split(',')[0] == '名詞':
            # 名詞かつ単語のみ格納する
            ret.append(node.feature.split(',')[-3].decode('utf-8'))
        node = node.next
    return ret

def main():
    bio = get_bio_from_txt('biolist.txt')
    
    # TfidfVectorizerでBag-of-Wordsモデルに変換
    vectorizer = TfidfVectorizer(analyzer=analyzer, max_df=MAX_DF)
    vectorizer.max_features = MAX_FEATURES
    X = vectorizer.fit_transform(bio)
 
    # LSAで次元削減
    lsa = TruncatedSVD(LSA_DIM)
    X = lsa.fit_transform(X)
    X = Normalizer(copy=False).fit_transform(X)
 
    # k-means法でクラスタリング
    if MINIBATCH:
        km = MiniBatchKMeans(n_clusters=NUM_CLUSTERS, init='k-means++', batch_size=1000, n_init=10, max_no_improvement=10, verbose=True)
    else:
        km = KMeans(n_clusters=NUM_CLUSTERS, init='k-means++', n_init=1, verbose=True)
    km.fit(X)
    labels = km.labels_
 
    transformed = km.transform(X)
    dists = np.zeros(labels.shape)
    for i in range(len(labels)):
        dists[i] = transformed[i, labels[i]]
 
    # クラスタの中心距離でソート
    clusters = []
    for i in range(NUM_CLUSTERS):
        cluster = []
        ii = np.where(labels==i)[0]
        dd = dists[ii]
        di = np.vstack([dd,ii]).transpose().tolist()
        di.sort()
        for d, j in di:
            cluster.append(bio[int(j)])
        clusters.append(cluster)
 
    return clusters

if __name__ == '__main__':
    clusters = main()
    filename = 'cluster_%d.txt' % NUM_CLUSTERS
    f = open(filename, 'w')
    for i,bio in enumerate(clusters):
        f.write('%d\n' % i)
        for bio in bio:
            f.write('%s' % (bio.replace('/n', '')))
        f.write('\n')
    f.close()
from app import app

from collections import defaultdict
import io
import Levenshtein
import os
import regex
import subprocess

basedir = app.config['BASEDIR'] or os.path.realpath(__file__)

def count_unique_words(myfile):
    cmd = 'grep -o "\\b[[:alnum:]]\\+\\b" {} |sort -f -u|wc -l'.format(myfile)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out = p.communicate()
    return int(out[0])

# Based on Rico Sennrich's implementation of chrF3 with fixed parameters
# Spaces, Beta = 3, ngram_size = 6
def chrF3(reference, hypothesis):
    def extract_ngrams(words, max_length=4, spaces=False):

        if not spaces:
            words = ''.join(words.split())
        else:
            words = words.strip()

        results = defaultdict(lambda: defaultdict(int))
        for length in range(max_length):
            for start_pos in range(len(words)):
                end_pos = start_pos + length + 1
                if end_pos <= len(words):
                    results[length][tuple(words[start_pos: end_pos])] += 1
        return results

    def get_correct(ngrams_ref, ngrams_test, correct, total):
        for rank in ngrams_test:
            for chain in ngrams_test[rank]:
                total[rank] += ngrams_test[rank][chain]
                if chain in ngrams_ref[rank]:
                    correct[rank] += min(ngrams_test[rank][chain], ngrams_ref[rank][chain])

        return correct, total

    def f1(correct, total_hyp, total_ref, max_length, beta=3, smooth=0):

        precision = 0
        recall = 0

        for i in range(max_length):
            if total_hyp[i] + smooth and total_ref[i] + smooth:
                precision += (correct[i] + smooth) / (total_hyp[i] + smooth)
                recall += (correct[i] + smooth) / (total_ref[i] + smooth)

        precision /= float(max_length)
        recall /= float(max_length)

        return (1 + beta**2) * (precision*recall) / ((beta**2 * precision) + recall), precision, recall

    ref = io.open(reference, "r")
    hyp = io.open(hypothesis, "r")

    correct = [0]*6
    total = [0]*6
    total_ref = [0]*6

    for line in ref:
      line2 = hyp.readline()

      ngrams_ref = extract_ngrams(line, max_length=6, spaces=False)
      ngrams_test = extract_ngrams(line2, max_length=6, spaces=False)

      get_correct(ngrams_ref, ngrams_test, correct, total)

      for rank in ngrams_ref:
          for chain in ngrams_ref[rank]:
              total_ref[rank] += ngrams_ref[rank][chain]

    chrf, precision, recall = f1(correct, total, total_ref, 6, 3)
    
    return chrf*100


def bleu(reference, hypothesis):
    cmd = 'java -Dfile.encoding=UTF8 -XX:+UseCompressedOops -Xmx2g -cp tercom-0.8.0.jar:multeval-0.5.1.jar:meteor-1.4.jar multeval.MultEval eval --refs {} --hyps-baseline {} --metrics bleu 2>&1| grep "[ ]AVG"| grep -o "[^ ]\+$"|sed "s%,%.%g"'
    wd  = os.path.join(basedir, "mteval-lite")
    p = subprocess.Popen(cmd.format(reference, hypothesis), shell=True, stdout=subprocess.PIPE, cwd=wd)
    out = p.communicate()
        
    return float(out[0])

def ter(reference, hypothesis):
    cmd = 'java -Dfile.encoding=UTF8 -XX:+UseCompressedOops -Xmx2g -cp tercom-0.8.0.jar:multeval-0.5.1.jar:meteor-1.4.jar multeval.MultEval eval --refs {} --hyps-baseline {} --metrics ter 2>&1| grep "[ ]AVG"| grep -o "[^ ]\+$"|sed "s%,%.%g"'
    wd  = os.path.join(basedir, "mteval-lite")
    p = subprocess.Popen(cmd.format(reference, hypothesis), shell=True, stdout=subprocess.PIPE, cwd=wd)
    out = p.communicate()
    return min(100.0,float(out[0]))

def beer(reference, hypothesis):
    cmd = "./beer -r {} -s {}"
    wd = os.path.join(basedir, "beer-lite")
    p = subprocess.Popen(cmd.format(reference, hypothesis), shell=True, stdout=subprocess.PIPE, cwd=wd)
    out = p.communicate()
    return min(100.0, 100*float(out[0].decode('utf-8').split(" ")[-1]))
    

def wer(reference, hypothesis):
    def word_to_char(mystr1, mystr2):
       base=20000
       index = {}
       res1 = []
       for i in mystr1.split():
           if i not in index:
               index[i] = base
               base += 1 
           res1.append(chr(index[i]))

       res2 = []
       for i in mystr2.split():
           if i not in index:
               index[i] = base
               base += 1 
           res2.append(chr(index[i]))

       return "a"+"".join(res1), "a"+"".join(res2)

    fo = io.open(reference, "r")
    fh = io.open(hypothesis, "r")


    res = []
    lens = []
    for i in fo:
        j = fh.readline()
        s1, s2 = word_to_char(i.strip(), j.strip())
        res.append(Levenshtein.distance(s1, s2))
        lens.append(len(s1))
    
    fo.close()
    fh.close()
    return min(100.0,sum(res)*100/float(sum(lens)))
        
def prepare_files(refi, hypi, refo, hypo, max_lines = 3000):
    fri = io.open(refi, "r", errors="ignore")
    fhi = io.open(hypi, "r", errors="ignore")
    fro = io.open(refo, "w")
    fho = io.open(hypo, "w")
    
    nlines = max_lines
    
    for i in fri:
        j = fhi.readline()
        i = i.strip()
        j = j.strip()
        
        if i != "" or j != "":
            nlines -= 1
            if nlines < 0:
                break
                
            i = regex.sub(r"[^\p{Alpha}0-9 ]", " \g<0> ", i)
            i = regex.sub(r"[ ]+", " ", i)
            j = regex.sub(r"[^\p{Alpha}0-9 ]", " \g<0> ", j)
            j = regex.sub(r"[ ]+", " ", j)

            fro.write("{}\n".format(i))
            fho.write("{}\n".format(j))
    
    fri.close()
    fhi.close()
    fro.close()
    fho.close()

if __name__ == '__main__':
    import tempfile
    import sys
    import locale
    
    n1 = tempfile.NamedTemporaryFile()
    n2 = tempfile.NamedTemporaryFile()
    l1 = n1.name
    l2 = n2.name
    n1.close()
    n2.close()

    prepare_files(sys.argv[1], sys.argv[2], l1, l2)
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    print(("BLEU {:2.2f}".format(bleu(l1,l2))))
    print(("TER {:2.2f}".format(ter(l1,l2))))
    print(("WER {:2.2f}".format(wer(l1,l2))))
    print(("chrF3 {:2.2f}".format(chrF3(l1,l2))))
    print(("BEER {:2.2f}".format(beer(l1,l2))))
    print((count_unique_words(sys.argv[1])))

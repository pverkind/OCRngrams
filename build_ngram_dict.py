import re
import os
from collections import defaultdict, deque, Counter
import json
from openiti.helper.ara import ar_tok
from openiti.helper.funcs import get_all_text_files_in_folder
import time

def count_bigrams(t, token_regex = ar_tok):
    """"""
    ngram_cnt = Counter()
    for m in re.finditer(t, token_regex):
        tok2 = tok1
        tok1 = m.group()
        if tok2:
            ngram_cnt["{} {}".format(tok1, tok2)] += 1
    return ngram_cnt

def count_ngrams(t, n=2, token_regex=ar_tok, ngram_cnt=Counter()):
    """Count the different ngrams in string `t`.

    Args:
        t (str): string in which the ngrams must be counted
        n (int): number of tokens in each ngram
        token_regex (str): regular expression that defines a token
        ngram_cnt (obj): collections.Counter() object

    Returns:
        dict (key: ngram, val: count)
    """
    #ngram_cnt = Counter()
    toks = deque([None]*n, maxlen=n)
    for m in re.finditer(token_regex, t):
        toks.append(m.group())
        try:
            ngram = " ".join(toks)  # will fail if toks still contains None value
            ngram_cnt[ngram] += 1
        except:
            continue
    return ngram_cnt

def count_ngrams_in_file(fp, n=2, header_splitter=None,
                         outfolder="ngrams_in_texts",
                         token_regex=ar_tok,
                         overwrite=False,
                         verbose=False):
    """Count distinct ngrams in the body of a text file\
    and save the count as a json file in `outfolder`.

    Args:
        fp (str): path to the text file
        header_splitter (str): string that indicates the boundary
            between a metadata header and the body text;
            if None, tokens will be counted from the start of the file
        outfolder (str): path to the folder where the output json file
            will be stored
        token_regex (str): regular expression to describe a single token
        overwrite (bool): if False, count data will be loaded from existing
            json file. If True, existing json files will be overwritten.

    Returns:
        collections.Counter object
    """
    start = time.time()
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    outfn = os.path.splitext(os.path.basename(fp))[0]
    outfp = os.path.join(outfolder, outfn+"_ngram_count.json")
    if overwrite or not os.path.exists(outfp):
        fc = Counter()
        with open(fp, mode="r", encoding="utf-8") as file:
            # start counting only after the header,
            #if a header_splitter is defined:
            start_counting = True
            if header_splitter:
                start_counting = False
            
            para = ""
            i = 0
            while True:
                line = file.readline()
                i += 1
                if not line:
                    break
                if not start_counting:  # line still in header
                    if header_splitter in line:
                        start_counting = True
                if start_counting:
                    if line.startswith("#"):
                        if para.strip():
                            #print(len(para))
                            count_ngrams(para, n=n, ngram_cnt=fc,
                                         token_regex=token_regex)
                            #r = input("Print para? Y/N")
                            #if r.lower() == "y":
                            #    print(para)
                            #    print(json.dumps(pc, ensure_ascii=False, indent=2))
                            para = line
                    else:
                        para += " " + line
                if verbose:
                    if not i%10000:
                        print(i, len(fc))
        if verbose:
            print(i, "lines")
            print("counting ngrams in {} took {} seconds".format(outfn, time.time()-start))
        with open(outfp, mode="w", encoding="utf-8") as file:
            json.dump(dict(fc), file, ensure_ascii=False, indent=2)
    else:
        with open(outfp, mode="r", encoding="utf-8") as file:
            fc = Counter(json.load(file))
        if verbose:
            print("loading ngram count from {} took {} seconds".format(outfn, time.time()-start))
    return fc

def join_ngram_counts(folder, outfp="total_counts.json",
                      input_threshold=1, output_threshold=1):
    """Join all ngram count json files inside a folder\
    including only keys that have a minimum value of `threshold`

    Args:
        folder (str): path to the folder containg the json files
        outfp (str): path to the file in which the compound count
            will be stored.
        input_threshold (int): only include an ngram from a text
            if that ngram has a count of at least `input_threshold`
            in that file.
        output_threshold (int): only include an ngram in the compound file
            if that ngram has a count of at least `output_threshold`
            in the compound dictionary count.
        
    """
    cnt = Counter()
    print("COMBINING COUNTS FROM BOOK JSONS:")
    for fn in os.listdir(folder):
        print("-", fn)
        fp = os.path.join(folder, fn)
        with open(fp, mode="r", encoding="utf-8") as file:
            d = json.load(file)
            #d = {k:v for k,v in d.items() if v >= input_threshold}
            cnt += Counter(d)
    #cnt = {k:v for k,v in cnt.items() if v >= output_threshold}
    with open(outfp, mode="w", encoding="utf-8") as file:
        json.dump(cnt, file, ensure_ascii=False, indent=2)
    
        

def count_ngrams_in_folder(folder, n=2, header_splitter=None,
                           outfolder="ngrams_in_texts",
                           token_regex=ar_tok,
                           overwrite=False,
                           input_threshold=1,
                           output_threshold=1
                           ):
    """Count distinct ngrams in the body of a text file\
    and save the count as a json file in `outfolder`.

    Args:
        fp (str): path to the text file
        header_splitter (str): string that indicates the boundary
            between a metadata header and the body text;
            if None, tokens will be counted from the start of the file
        outfolder (str): path to the folder where the output json file
            will be stored
        token_regex (str): regular expression to describe a single token
        overwrite (bool): if False, count data will be loaded from existing
            json file. If True, existing json files will be overwritten.
        input_threshold (int): only include an ngram from a text
            if that ngram has a count of at least `input_threshold`
            in that file.
        output_threshold (int): only include an ngram in the compound file
            if that ngram has a count of at least `output_threshold`
            in the compound dictionary count.

    Returns:
        collections.Counter object
    """
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    for fp in get_all_text_files_in_folder(folder):
        print(os.path.basename(fp))
        count_ngrams_in_file(fp, n=n, header_splitter=header_splitter,
                             outfolder=outfolder, token_regex=token_regex,
                             overwrite=False)
    outfn = os.path.basename(folder)
    join_ngram_counts(outfolder, outfp=outfn+"_ngram_count.json",
                      input_threshold=input_threshold,
                      output_threshold=output_threshold)



fp = r"D:\London\OpenITI\25Y_repos\0650AH\data\0626YaqutHamawi\0626YaqutHamawi.MucjamBuldan\0626YaqutHamawi.MucjamBuldan.Shamela0023735-ara1.completed"
fp = r"D:\London\OpenITI\25Y_repos\0650AH\data\0626YaqutHamawi\0626YaqutHamawi.MucjamUdaba\0626YaqutHamawi.MucjamUdaba.Shamela0009788-ara1.mARkdown"
outfolder = "ngrams_in_texts"
if not os.path.exists(outfolder):
    os.makedirs(outfolder)
##count_ngrams_in_file(fp, n=2,
##                     header_splitter="#META#Header#End",
##                     outfolder=outfolder,
##                     token_regex=ar_tok,
##                     overwrite=False)
##
##join_ngram_counts(outfolder)

##folder = r"D:\London\OpenITI\25Y_repos\0600AH"
##outfolder = r"ngrams_in_texts\0600AH"
##count_ngrams_in_folder(folder, n=2,
##                       header_splitter="#META#Header#End",
##                       outfolder=outfolder,
##                       token_regex=ar_tok,
##                       overwrite=False,
##                       input_threshold=0,
##                       output_threshold=1
##                       )
for i in range(726, 1501):
    if not i % 25:
        folder = r"D:\London\OpenITI\25Y_repos\{:04d}AH".format(i)
        outfolder = r"ngrams_in_texts\{:04d}AH".format(i)
        print(outfolder)
        count_ngrams_in_folder(folder, n=2,
                               header_splitter="#META#Header#End",
                               outfolder=outfolder,
                               token_regex=ar_tok,
                               overwrite=False
                               )
        
folder = r"D:\London\OpenITI\25Y_repos\9001AH"
outfolder = r"ngrams_in_texts\9001AH"
count_ngrams_in_folder(folder, n=2,
                       header_splitter="#META#Header#End",
                       outfolder=outfolder,
                       token_regex=ar_tok,
                       overwrite=False
                       )
        

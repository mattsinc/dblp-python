import dblp
import jellyfish
import time

#inFile = open('dump-test.txt', mode = 'r')
inFile = open('dump-sorted-uniq.txt', mode = 'r')
lines = inFile.read()
print(lines)
inFile.close()
myAuthors = []
count = 0

# # parse each line
# #for currLine in lines:
# #    # make sure line not empty
# #    if (currLine):
# #        print("Next line: "+str(currLine))
#         # commas immediately after ' denote new author
# #        currLineCommaSep = currLine.split("'")
#         # split on non-espcaped '
#         currLineCommaQuoteSep = currLineCommaSep#[i.split("\'") for i in currLineCommaSep]
#         print("Comma, quote separated: "+str(currLineCommaQuoteSep))
#         # parse input -- everything between non-escaped quotes is a new author to add to list
#         for newAuthor in currLineCommaQuoteSep:
#             print("Found author #"+str(count)+" : "+str(newAuthor))
#             # add each author to list
#             myAuthors.append(newAuthor)
#             count = count + 1
#             print("") # empty line between

# split on non-espcaped '
currLineCommaSep = lines.split(", ")
print("Quote separated: "+str(currLineCommaSep))
# parse input -- everything between non-escaped quotes is a new author to add to list
for newAuthor in currLineCommaSep:
    if (newAuthor is not "" and newAuthor is not "\n" and not("," in newAuthor)):
        print("Found author #"+str(count)+" : "+str(newAuthor))
        # add each author to list
        myAuthors.append(newAuthor.strip())
        count = count + 1
        #print("") # empty line between

#print("Total Authors: "+str(len(myAuthors)))
numAuthors = len(myAuthors)
# now that we have all authors, run deduplication -- print out likely matches
for currAuthor in range(numAuthors):
    restOfAuthors = currAuthor + 1
    # compare author with all subsequent authors, searching for close matches
    while (restOfAuthors < numAuthors):
        #print("Comparing "+str(currAuthor)+" to "+str(restOfAuthors))
        similarity = jellyfish.jaro_winkler_similarity(myAuthors[currAuthor], myAuthors[restOfAuthors])
        # arbitrary threshold at the moment -- anectdotally, anything less than this leads to a large number of false positives
        if (similarity > 0.94):
            print("Similarity ("+str(similarity)+"): "+myAuthors[currAuthor]+", "+myAuthors[restOfAuthors])
        restOfAuthors += 1

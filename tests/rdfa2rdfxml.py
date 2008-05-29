#!/usr/bin/env python
# 
# This file is part of librdfa.
# 
# librdfa is Free Software, and can be licensed under any of the
# following three licenses:
# 
#   1. GNU Lesser General Public License (LGPL) V2.1 or any 
#      newer version
#   2. GNU General Public License (GPL) V2 or any newer version
#   3. Apache License, V2.0 or any newer version
# 
# You may not use this file except in compliance with at least one of
# the above three licenses.
# 
# See LICENSE-* at the top of this software distribution for more
# information regarding the details of each license.
# 
# Reads in an XHTML+RDFa file and outputs the triples generated by the file
# in N3 format.
import sys, os, urllib2
sys.path += ("../python/dist",)
import rdfa
from StringIO import StringIO
from rdflib.Graph import ConjunctiveGraph

URL_TYPE_HTTP = 1
URL_TYPE_FILE = 2

##
# Called whenever a triple is generated by the underlying implementation.
#
# @param rdf the rdf object to use when storing data.
# @param subject the subject of the triple.
# @param predicate the predicate for the triple.
# @param obj the object of the triple.
# @param objectType the type for the object in the triple.
# @param dataType the dataType for the object in the triple.
# @param language the language for the object in the triple.
def handleTriple(rdf, subject, predicate, obj, objectType, dataType,
                  language):
    
    if(objectType == rdfa.RDF_TYPE_NAMESPACE_PREFIX):
        rdf['namespaces'][predicate] = obj
    else:
        rdf['triples'].append(
            (subject, predicate, obj, objectType, dataType, language))
        
##
# Called whenever the processing buffer for the C-side needs to be re-filled.
#
# @param dataFile the file-like object to use when reading in the data stream.
# @param bufferSize the size of the buffer to return. Returning anything less
#                   than bufferSize will halt execution after the returned
#                   buffer has been processed.
def fillBuffer(dataFile, bufferSize):
    return dataFile.read()

def objectToN3(obj, objectType, dataType, language):
    rval = ""
    
    if(objectType in (rdfa.RDF_TYPE_PLAIN_LITERAL,
                      rdfa.RDF_TYPE_TYPED_LITERAL,
                      rdfa.RDF_TYPE_XML_LITERAL)):
        rval += "\"%s\"" % \
                (obj.replace("\"", "\\\"").replace("\n", "\\n"),)
    elif(objectType == rdfa.RDF_TYPE_IRI):
        rval += "<%s>" % (obj,)

    if(language and (objectType == rdfa.RDF_TYPE_PLAIN_LITERAL)):
        rval += "@%s" % (language,)

    if(objectType == rdfa.RDF_TYPE_TYPED_LITERAL):
        rval += "^^<%s>" % (dataType,)
    elif(objectType == rdfa.RDF_TYPE_XML_LITERAL):
        rval += "^^<http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral>"

    return rval

##
# Converts a bnode to a N3 formatted string.
#
# @param obj the object of the triple.
# @param triples the triple store.
# @param processed all of the subjects that have already been processed.
#
# @return an N3 formatted string.
def bnodeToN3(triples, processed, allTriples):
    print "bnodeToN3", triples
    rval = "[ "

    # Print all subjects with URIs first
    previousTriple = False
    for triple in triples:
        subject = triple[0]
        predicate = triple[1]
        obj = triple[2]
        objectType = triple[3]
        dataType = triple[4]
        language = triple[5]

        #print "STO:", triple
        if(previousTriple):
            rval += "; "
        else:
            previousTriple = True

        if(obj.startswith("_:") and obj not in processed):
            objectTriples = getTriplesBySubject(obj, allTriples)
            rval += "<%s> %s" % \
                (predicate, bnodeToN3(objectTriples, processed, allTriples))
        elif(subject not in processed):
            rval += "<%s> %s" % \
                (predicate, objectToN3(obj, objectType, dataType, language))
    
    rval += " ]"

    processed.append(triples[0][0])

    return rval

##
# Converts a triple to a N3 formatted string.
#
# @param subject the subject of the triple.
# @param predicate the predicate for the triple.
# @param obj the object of the triple.
# @param objectType the type for the object in the triple.
# @param dataType the dataType for the object in the triple.
# @param language the language for the object in the triple.
# @param processed all of the bnodes that have already been processed.
#
# @return an N3 formatted string.
def tripleToN3(triples, processed, allTriples):
    rval = ""

    for triple in triples:
        subject = triple[0]
        predicate = triple[1]
        obj = triple[2]
        objectType = triple[3]
        dataType = triple[4]
        language = triple[5]
        
        rval += "<%s> <%s> " % (subject, predicate)

        #print "PROCESSED:", processed

        if(obj.startswith("_:")):
            bnodeTriples = getTriplesBySubject(obj, allTriples)
            rval += bnodeToN3(bnodeTriples, processed, allTriples)
        else:
            rval += objectToN3(obj, objectType, dataType, language)
            
        rval += " .\n"

    return rval

##
# Gets the non-bnode subjects that are in the triple store.
#
# @param triples the triple store.
#
# @return all of the non-bnode subjects in the triple store.
def getNonBnodeSubjects(triples):
    rval = {}
    
    for triple in triples:
        subject = triple[0]
        if(not subject.startswith("_:")):
            rval[subject] = True

    return rval.keys()

##
# Gets the bnode subjects that are in the triple store.
#
# @param triples the triple store.
#
# @return all of the bnode subjects in the triple store.
def getBnodeSubjects(triples):
    rval = {}
    
    for triple in triples:
        subject = triple[0]
        if(subject.startswith("_:")):
            rval[subject] = True

    rval = rval.keys()
    rval.sort()

    return rval

##
# Gets the triples by subject.
#
# @param subject The subject to use when retrieving the triples.
#
# @return A list of all triples that match a given subject.
def getTriplesBySubject(subject, triples):
    rval = []

    for triple in triples:
        if(triple[0] == subject):
            rval.append(triple)

    return rval

##
# Gets RDF/XML given an object with pre-defined namespaces and triples.
#
# @param rdf the rdf dictionary object that contains namespaces and triples.
#
# @return the RDF/XML text.
def getRdfXml(rdf):
    n3 = ""
    
    # Append the RDF namespace and print the prefix namespace mappings
    rdf['namespaces']['xh1'] = "http://www.w3.org/1999/xhtml/vocab#"
    rdf['namespaces']['rdf'] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    for prefix, uri in rdf['namespaces'].items():
        n3 += "@prefix %s: <%s> .\n" % (prefix, uri)
        
    # Print each subject-based triple to the screen
    triples = rdf['triples']
    processed = []

    # Get all of the non-bnode subjects
    nonBnodeSubjects = getNonBnodeSubjects(triples)

    # Get all of the bnode subjects
    bnodeSubjects = getBnodeSubjects(triples)

    for subject in nonBnodeSubjects:
        subjectTriples = getTriplesBySubject(subject, triples)
        #print "PROCESSING NB SUBJECT:", subjectTriples

        if(subject not in processed):
            n3 += tripleToN3(subjectTriples, processed, triples)
        processed.append(subject)

    for subject in bnodeSubjects:
        subjectTriples = getTriplesBySubject(subject, triples)
        #print "PROCESSING BN SUBJECT:", subject
        if(subject not in processed):
            n3 += bnodeToN3(subjectTriples, processed, triples)
            n3 += " .\n"

    #print n3

    g = ConjunctiveGraph()
    g.parse(StringIO(n3), format="n3")
    rdfxml = g.serialize()

    return rdfxml

##
# The main entry point for the script.
#
# @param argv the argument list passed to the program.
# @param stdout the standard output stream assigned to the program.
# @param environ the execution environment for the program.
def main(argv, stdout, environ):
    urlType = URL_TYPE_FILE

    if((len(argv) > 1) and (len(argv[1]) > 4)):
        if(argv[1][:5] == "http:"):
            urlType = URL_TYPE_HTTP
    else:
        print "usage:", argv[0], "<file>"
        print "or"
        print "      ", argv[0], "<URL>"
        sys.exit(1)
    
    if((urlType == URL_TYPE_FILE) and (not os.path.exists(argv[1]))):
        print "File %s, does not exist" % (argv[1])
        sys.exit(1)
    if((urlType == URL_TYPE_FILE) and (not os.access(argv[1], os.R_OK))):
        print "Cannot read file named %s" % (argv[1])
        sys.exit(1)

    # Open the data file and setup the parser
    dataFile = None
    parser = None

    # Open the proper file stream and initialize the parser using the URL
    if(urlType == URL_TYPE_HTTP):
        dataFile = urllib2.urlopen(argv[1])
        parser = rdfa.RdfaParser(argv[1])
    else:
        dataFile = open(argv[1], "r")
        parser = rdfa.RdfaParser("file://" + os.path.abspath(argv[1]))

    # Create the RDF dictionary that will be used by the triple handler
    # callback
    rdf = {}
    rdf['namespaces'] = {}
    rdf['triples'] = []

    # Setup the parser
    parser.setTripleHandler(handleTriple, rdf)
    parser.setBufferHandler(fillBuffer, dataFile)

    # Parse the document
    parser.parse()

    # Close the datafile
    dataFile.close()

    # Print the RDF/XML to stdout
    print getRdfXml(rdf)

##
# Run the rdfa2n3 python application.
if __name__ == "__main__":
    main(sys.argv, sys.stdout, os.environ)

#!/usr/bin/env python
#
# Copyright 2008 Digital Bazaar, Inc.
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
import sys, os
sys.path += ("../python/dist",)
import rdfa

##
# Formats a triple in a very special way.
#
# @param n3 the HTTP request to use when writing the output.
# @param subject the subject of the triple.
# @param predicate the predicate for the triple.
# @param obj the object of the triple.
# @param object_type the type for the object in the triple.
# @param datatype the datatype for the object in the triple.
# @param language the language for the object in the triple.
def write_triple( \
    n3, subject, predicate, obj, object_type, datatype, language):
    print "<%s>" % (subject,)
    print "   <%s>" % (predicate,)
    if(object_type == rdfa.RDF_TYPE_IRI):
        print "      <%s> . " % (obj,)
    else:
        ostr = "      \"%s\"" % (obj,)
        if(language != None):
            ostr += "@%s" % (language,)
        if(datatype != None):
            ostr += "^^^<%s>" % (datatype,)
        print ostr + " ."

##
# Called whenever a triple is generated for the default graph by the 
# underlying implementation.
#
# @param n3 the output buffer
# @param subject the subject of the triple.
# @param predicate the predicate for the triple.
# @param obj the object of the triple.
# @param object_type the type for the object in the triple.
# @param datatype the datatype for the object in the triple.
# @param language the language for the object in the triple.
def default_triple( \
    n3, subject, predicate, obj, object_type, datatype, language):

    write_triple( \
        n3, subject, predicate, obj, object_type, datatype, language)

##
# Called whenever a triple is generated for the processor graph by the 
# underlying implementation.
#
# @param n3 the output buffer
# @param subject the subject of the triple.
# @param predicate the predicate for the triple.
# @param obj the object of the triple.
# @param object_type the type for the object in the triple.
# @param datatype the datatype for the object in the triple.
# @param language the language for the object in the triple.
def processor_triple( \
    n3, subject, predicate, obj, object_type, datatype, language):
    
    if(object_type == rdfa.RDF_TYPE_NAMESPACE_PREFIX):
        print "%s %s: <%s> ." % (subject, predicate, obj)
    else:
        write_triple( \
            n3, subject, predicate, obj, object_type, datatype, language)

##
# Called whenever the processing buffer for the C-side needs to be re-filled.
#
# @param dataFile the file-like object to use when reading in the data stream.
# @param bufferSize the size of the buffer to return. Returning anything less
#                   than bufferSize will halt execution after the returned
#                   buffer has been processed.
def handle_buffer(dataFile, bufferSize):
    return dataFile.read(bufferSize)

##
# The main entry point for the script.
#
# @param argv the argument list passed to the program.
# @param stdout the standard output stream assigned to the program.
# @param environ the execution environment for the program.
def main(argv, stdout, environ):
    print "creating parser"
    parser = rdfa.RdfaParser("http://www.w3.org/2006/07/SWD/RDFa/testsuite/xhtml1-testcases/0001.xhtml")

    print "opening", argv[1]
    data_file = open(argv[1], "r")
    n3 = ""
    
    print "created parser"
    parser.setDefaultGraphTripleHandler(default_triple, n3)
    print "set default graph triple handler"
    parser.setProcessorGraphTripleHandler(processor_triple, n3)
    print "set processor graph triple handler"
    parser.setBufferHandler(handle_buffer, data_file)
    print "set buffer handler"

    print "parsing..."
    parser.parse()
    print "completed parsing"
    data_file.close()
    
##
# Run the rdfa2n3 python application.
if __name__ == "__main__":
    main(sys.argv, sys.stdout, os.environ)

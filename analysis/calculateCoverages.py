

import re, argparse, os, json, sys, math

import coloredPixelCounter
from coloredPixelCounter import calculateCoverage

import cinemaFileIterator
from cinemaFileIterator import cinemaFileIterator, buildCinemaPath, getOrderedVariableNames

from base64Mappings import o2b


# =============================================================================
# Write out the histogram files in the format required by cinema chart/search
# =============================================================================
def writeHistogramFiles(outputDir, histograms):
    # Now write out the histograms
    for key in histograms:
        histogram = histograms[key]

        images = []
        series = []

        for i in xrange(len(histogram['counts'])):
            series.append({ 'x': i + 1, 'y': histogram['counts'][i] })
            images.append({ key: histogram['images'][i] })

        resultObj = { 'series': [ { 'data': series,
                                    'name': key } ],
                      'images': images }

        outputFilePath = os.path.join(outputDir, key)
        if not os.path.exists(outputFilePath):
            os.makedirs(outputFilePath)

        seriesFile = os.path.join(outputFilePath, 'histogram.json')
        with open(seriesFile, 'w') as fd:
            json.dump(resultObj, fd)


# =============================================================================
# Iterate over the cinema dataset, generating one histogram file for every
# possible combination of arguments (not including time, theta, or phi).
# =============================================================================
def calculateCoverages(namePattern, arguments):
    variablesList = getOrderedVariableNames(namePattern)
    layerComponents = [ i for i in variablesList if i not in ['time', 'phi', 'theta'] ]

    # This loop assigns base64 encodings to each value in each of the arguments,
    # not including 'time', 'phi', or 'theta'.  Then these encoding values are
    # put together to uniquely identify any combination of the argument values that
    # will be compact and reproducible.
    valueCodes = {}
    for component in layerComponents:
        valuesList = arguments[component]['values']
        valueCodes[component] = { valuesList[j]: o2b[j] for j in xrange(len(valuesList)) }

    histObj = {}

    # This loop iterates over all the images in a particular cinema dataset,
    # calculating the percent pixel coverage for each one, and then dropping
    # counts and the corresponding images into one of a hundred bins.
    for fileIdx, currentValues in cinemaFileIterator(namePattern, arguments):

        try:
            # Take the dictionary of values for the current iterator element, and
            # convert it into the path to the image file.
            relativePath = buildCinemaPath(namePattern, currentValues)

            # Create an ordered list of the base64 encoded representations of
            # each of the current values from the iterator
            layerEncodingList = [ valueCodes[component][currentValues[component]] for component in layerComponents ]

            # Make a string out of the ordered list created above, separated by a '-'
            layerEncoding = '-'.join(layerEncodingList)

            # Use the file path to image to read that image and get the percent coverage
            percentCoverage = calculateCoverage(os.path.join(args.rootdir, relativePath), [255,255,255])

            if layerEncoding not in histObj:
                histObj[layerEncoding] = { 'counts': [ 0 for i in xrange(100) ],  # Create 100 empty bins
                                           'images': [ [] for j in xrange(100)] }

            # Increment the counter in the appropriate bin, and add this image
            # ordinal to the list in that bin as well.
            binNumber = int(math.floor(percentCoverage))
            histObj[layerEncoding]['counts'][binNumber] += 1
            histObj[layerEncoding]['images'][binNumber].append(fileIdx)

            print 'ordinal: ',fileIdx,', path: ',relativePath,', encoding: ',layerEncoding,', percent coverage: ',percentCoverage

        except KeyboardInterrupt:
            # This exception handler is useful for testing so you don't have to wait
            # for the entire dataset to be processed before seeing any results.
            print 'Caught keyboard interrupt, writing histogram object now'
            writeHistogramFiles(args.outdir, histObj)
            sys.exit(0)

    # Now that we have gone through the entire dataset, write out all the histograms
    writeHistogramFiles(args.outdir, histObj)


# =============================================================================
# Main entry point
# =============================================================================
if __name__ == "__main__":
    description = "Go through a cinema dataset and calculate percent coverage for each image"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--rootdir", type=str, default="", help="Path to root of data set (where info.json lives)")
    parser.add_argument("--outdir", type=str, default=os.getcwd(), help="Path to directory where output should be written")
    args = parser.parse_args()

    infojson = os.path.join(args.rootdir, 'info.json')

    json_data = None
    with open(infojson, 'r') as fd:
        json_data = json.load(fd)

    namePattern = json_data['name_pattern']
    arguments = json_data['arguments']

    calculateCoverages(namePattern, arguments)

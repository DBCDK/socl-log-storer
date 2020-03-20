#!/usr/bin/env python3

# This script filters json log lines, and dumps and tgz them.


import argparse
import code
import datetime
import json
import os
import re
import signal
import sys
import traceback
import fileinput
import zipfile

signal.signal(signal.SIGUSR2, lambda sig, frame: code.interact())
# The three lines above allows this program to be interrupted at any point with
# kill -SIGUSR2 <PID> and present an interactive console for debugging.
# More info: https://stackoverflow.com/a/4693529

################################################################################
# GLOBAL STUFF
################################################################################

# Some global variables that is mostly to handle default values.

# The name of our script - used in output.
script_name = "filter-log"

# These are convenient to not have to pass to all functions, etc.
# Could have been wrapped in a class, though.
do_debug = False
do_trace = False


################################################################################
# LOG AND OUTPUT STUFF
################################################################################

# I can't figure out how to make this a (static) method in Colors, that can be called by attributes init.
def build_color(num):
    return '\033[' + str(num) + 'm'


class Colors:
    # Control
    NORMAL = build_color(0)
    BOLD = build_color(1)
    UNDERLINE = build_color(4)
    # Colors
    GREEN = build_color(92)
    BLUE = build_color(34)
    YELLOW = build_color(93)
    RED = build_color(91)
    CYAN = build_color(96)
    MAGENTA = build_color(95)
    # Name is script name, rest is levels
    NAME = GREEN
    INFO = GREEN
    WARN = YELLOW
    DRYRUN = YELLOW
    ERROR = RED
    DEBUG = CYAN
    TRACE = MAGENTA
    UNKNOWN = RED
    STAGENAME = BLUE
    CHECKNAME = GREEN

    @staticmethod
    def remove_colors(string: str):
        """
        Remove any color codes from a string, making it suitable for output to file, instead of terminal.
        :param string: The string to remove color codes from.
        :return: The input string, with color codes removed.
        """
        return re.sub('\\033\\[\\d{1,2}m', '', string)


def output_log_msg(msg: str) -> None:
    print(msg, flush=True)


def format_log_msg(level: str, msg: str) -> str:
    """
    Format a string for log output. The level is colorized, if we are in an ssty.
    The datetime added, is localtime.
    :param level: The level (INFO, WARN, DEBUG, ...)
    :param msg: The msg to output_msg.
    :return: A formatted string.
    """
    output = Colors.NAME + "[" + script_name + "] " + Colors.NORMAL + datetime.datetime.now().strftime("%T.%f") + " "
    if level == "DEBUG":
        output += Colors.DEBUG
    elif level == "TRACE":
        output += Colors.TRACE
    elif level == "INFO":
        output += Colors.INFO
    elif level == "DRYRUN":
        output += Colors.DRYRUN
    elif level == "WARN":
        output += Colors.WARN
    elif level == "ERROR":
        output += Colors.ERROR
    elif level == "TODO":
        output += Colors.YELLOW
    else:
        output += Colors.UNKNOWN
    output += level + Colors.NORMAL + ": " + msg
    if sys.stdout.isatty():
        return output
    else:
        return Colors.remove_colors(output)


def info(msg: str) -> None:
    """
    Output a msg at LOG level.
    :param msg: The message to output.
    """
    output_log_msg(format_log_msg("INFO", msg))


def warn(msg: str) -> None:
    """
    Output a msg at WARN level.
    :param msg: The message to output.
    """
    output_log_msg(format_log_msg("WARN", msg))


def dryrun(msg: str) -> None:
    """
    Output a msg at DRYRUN level.
    :param msg: The message to output.
    """
    output_log_msg(format_log_msg("DRYRUN", msg))


def error(msg: str) -> None:
    """
    Output a msg at ERROR level.
    :param msg: The message to output.
    """
    output_log_msg(format_log_msg("ERROR", msg))


def trace(prefix="") -> None:
    """
    Output a trace at TRACE level, if the global variable "do_trace" is True
    :param: Optional parameter to set before the func name. This can be used by e.g. classes.
    """
    global do_trace
    if do_trace:
        top = traceback.extract_stack(None, 2)[0]
        func_name = top[2]
        output_log_msg(format_log_msg("TRACE", "Entering " + prefix + func_name))


def todo(msg: str) -> None:
    """
    Output a msg at TODO level, if the global variable "do_debug" is True
    :param msg: The message to output.
    """
    global do_debug
    if do_debug:
        output_log_msg(format_log_msg("TODO", msg))


def debug(msg: str) -> None:
    """
    Output a msg at DEBUG level, if the global variable "do_debug" is True
    :param msg: The message to output.
    """
    global do_debug
    if do_debug:
        output_log_msg(format_log_msg("DEBUG", msg))

def verbose(msg: str) -> None:
    """
    Output a msg at DEBUG level, if the global variable "do_debug" is True
    :param msg: The message to output.
    """
    global do_debug
    if do_debug:
        output_log_msg(format_log_msg("DEBUG", msg))


################################################################################
# PARSE ARGS AND MAIN
################################################################################
def regexp(astring):
    try:
        re.compile(astring)
        return astring
    except re.error:
        raise argparse.ArgumentTypeError("Argument must be a valid regular expression: " + astring)


def get_args() -> argparse.Namespace:
    """
    Configure the argument parsing system, and run it, to obtain the arguments given on the commandline.
    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--debug", action="store_true",
                        help="Output extra debug information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Output extra verbose information. Implies --debug")
#    parser.add_argument("-g", "--groups", default="",
#                        type=regexp,
#                        help="Use groups for some components. [<none>]")
    parser.add_argument("-o", "--output",
                        type=str,
                        default="log",
                        help="Stem of output file [log]")
    parser.add_argument("-f", "--folder",
                        type=str,
                        default=".",
                        help="Folder to write logfiles to [.]")
    parser.description = "Filter kafka json lines, extract key entries from message field, and write to 'rotated' files."
    parser.epilog = """
Examples:
    TBD:
    """ + sys.argv[0] + """ 

"""
    args = parser.parse_args()
    return args

def main():
    start_time = datetime.datetime.now()
    try:
        global script_name
        args = get_args()

        global do_debug
        global do_trace
        global do_dryrun
        do_debug = args.debug
        # do_trace = args.trace
        do_verbose = args.verbose
        if do_verbose:
            do_debug = True

        debug("cli options: debug:" + str(do_debug)
              + ", verbose: " + str(do_verbose)
              + ", output: " + str(args.output)
              + ", folder: " + str(args.folder)
              )

        message_rx = re.compile("\s+")
        output_file = None
        filename = None
        for line in fileinput.input('-'):

            try:
                line = line.strip()
                # Check if this is an empty line
                if not line:
                    continue
                blob = json.loads(line)
            except ValueError as e:
                # Best effort - or should we write this?
                warn("Couldn't parse this line: '" + line + "' - skipping it")
                warn("Error messages was: " + str(e))
                continue

            # For now, extract
            # We only keep lines that does not have "distrib=false" in the message
            if not "message" in blob:
                warn("A message was not found in the json string: '" + line + "'")
                warn("Line is ignored!")
                continue

            message = blob["message"]

            if "distrib=false" in message:
                verbose("Skipping entry where message contains distrib=false: '" + message + "'")
                continue
            # We also skip lines that does not have a webapp=/solr entry
            if not "webapp=/solr" in message:
                verbose("Skipping entry where message does not contain webapp=/solr: '" + message + "'")
                continue

            # Extract the timestamp and other fields.
            if not "timestamp" in blob:
                warn("A timestamp was not found in the json string: '" + line + "'")
                warn("Line is ignored!")
                continue
            timestamp = blob["timestamp"]

            # Need to
            # a: Parse the other fields in the message field - note, sometimes hits are not present, etc.
            try:
                debug("Message " + message)

                # TODO split does not handle spaces inside params e.g. params value for path=/update calls
                # TODO optional: move before distrib=false test. Reuse processing to determine distrib elements
                msg = message_rx.split(message)

                debug("Message json " + json.dumps(msg, indent=4))
                for pair in msg:
                    if '=' in pair:
                        elements = pair.split("=", 1)
                        #debug("pair " + pair + ", len = " + str(len(elements)))
                        if (len(elements) == 2):
                            key = elements[0]
                            value = elements[1]
                            #debug(key + " = " + value)
                            blob[key] = value

                            # parse params values
                            if key == "params":
                                try:
                                    # trim first and last character {} og JSON. TODO: assumes both are here, else it trims wrong character
                                    parameters = value[1:-1]

                                    params_values = {}

                                    # TODO: url decode in stead of split on &? Do we need to handle escaped & characters?
                                    for param_pair in parameters.split("&"):
                                        # Is is a key/value pair?
                                        if '=' in param_pair:
                                            param_elements = param_pair.split("=", 1)
                                            if (len(param_elements) == 2):
                                                # multiple values fields, use arrays.
                                                # TODO: do multiple values automatically? It would mean that output may have either string or string array
                                                if param_elements[0] in ("fl", "fq", "facet.field", "bq"):
                                                    # Add array
                                                    if param_elements[0] not in params_values:
                                                        params_values[param_elements[0]] = []

                                                    # skip empty string
                                                    if param_elements[1]:
                                                        params_values[param_elements[0]].append(param_elements[1])
                                                else:
                                                    if param_elements[0] in params_values:
                                                        # value should be added to multiple values fields.
                                                        warn("value %s in %s has multiple values"%(param_elements[1], param_elements[0]))
                                                    # overwrite if multiple values
                                                    params_values[param_elements[0]] = param_elements[1]

                                                # TODO: parse fq filter query into rec.collectionIdentifier?

                                    blob["params_values"] = params_values

                                except ValueError as e:
                                    warn("params could not be parsed - skipping line")
                                    continue

            except Exception as e:
                warn("No message in json string: '" + line + "'")
                continue

            # b: Find an appId in the url field (name?), if present, otherwise, set it to "" (empty string)
            appId = ""
            if "params_values" in blob and "appId" in blob["params_values"]:
                appId = blob["params_values"]["appId"]
                debug("appId " + appId)
            blob["appId"] = appId

            # c: Calculate startime, from timestamp - QTime (qtime is in ms)
            # TODO Handle timezone ? ( .tzinfo field in datetime object)
            calltime = None
            ts_format = '%Y-%m-%dT%H:%M:%S.%f+00:00'
            ts = datetime.datetime.strptime(timestamp, ts_format)
            if "QTime" in blob:

                calltime = ts - datetime.timedelta(milliseconds=int(blob["QTime"]))
                blob["calltime"] = calltime.strftime(ts_format)

            # d: Write to files
            if calltime:
                # Save file for each hour
                timestamp_str = ts.strftime("%Y-%m-%dT%H")

                # Save file for each minute
                #timestamp_str = ts.strftime("%Y-%m-%dT%H:%M")

                if not output_file:
                    # Use the timestamp of the first recorded entry in filename
                    filename = "socl-output-%s.jsonl"%timestamp_str
                    info("Create a new output file %s"%filename)
                    output_file = open(os.path.join(args.folder, filename), "a")

                if output_file:
                    # e: split files

                    # NOTE records may are not in order.
                    # Workaround: use < for file compare. Ignore that a few timestamp entries end in the wrong filename
                    new_filename = "socl-output-%s.jsonl"%timestamp_str
                    if filename < new_filename:
                        info("Create new file. New: %s, Close: %s" % (new_filename, filename))
                        output_file.close()

                        # f: zip files
                        zfile = zipfile.ZipFile(os.path.join(args.folder, filename + ".zip" ), 'w', zipfile.ZIP_DEFLATED)
                        filepath = os.path.join(args.folder, filename)
                        zfile.write(filepath, filename);
                        zfile.close();
                        os.remove(filepath);
                        filename = new_filename
                        output_file = open(os.path.join(args.folder, filename), "a")

                # d.1 Only select, export, query calls
                if "path" in blob and blob["path"] in ("/select", "/export", "/query"):
                    output_file.write( json.dumps(blob, indent=4) + "\n\n")

            debug("Blob " + json.dumps(blob, indent=4))


        info("Done")
        stop_time = datetime.datetime.now()
        info("Time passed: " + str(stop_time - start_time))

    except Exception:
        output_log_msg(traceback.format_exc())
        stop_time = datetime.datetime.now()
        info("Time passed: " + str(stop_time - start_time))
        error("Process failed " + Colors.RED + "FAILED" + Colors.NORMAL +
              " due to internal error (unhandled exception). Please file a bug report.")
        sys.exit(2)
    finally:

        if output_file:
            info("Close output file %s"%output_file)
            output_file.close()

        if filename:
            # Close last zip file
            zfile = zipfile.ZipFile(os.path.join(args.folder, filename + ".zip" ), 'w', zipfile.ZIP_DEFLATED)
            filepath = os.path.join(args.folder, filename)
            zfile.write(filepath, filename);
            zfile.close();
            os.remove(filepath);


main()

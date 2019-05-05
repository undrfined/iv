from lxml import html
from lxml import etree
from os import listdir
from os.path import isfile, join
import json
import ctypes
import argparse
import re
import colorama
from colorama import Fore, Back, Style
import shutil
from math import floor


def centerText(s):
    size = shutil.get_terminal_size((80, 20)).columns - 1
    return s.center(size, " ")


if __name__ == '__main__':
    colorama.init()

    parser = argparse.ArgumentParser(description='XPath console for cached html pages')
    parser.add_argument('domain', metavar='domain', type=str, help='domain to check')
    parser.add_argument('--ignore', '-i', help='regex with links to ignore (file or string)', nargs='+')
    args = parser.parse_args()

    ignore = ""
    try:
        c = open(args.ignore[0], "r")
        ignore = c.read()
        ignore = ignore.split("\n")
        c.close()
    except Exception as ex:
        ignore = args.ignore
    if ignore is None:
        ignore = []
    print(f"ignore: {ignore}")

    mypath = f"pages/{args.domain}/"
    manifest = mypath + "url_list.json"
    f = open(manifest, "r")
    manifest = json.loads(f.read())
    f.close()
    while True:
        xpath = input()
        try:
            pc = False
            supported = []
            attribute = "class"
            if "~" in xpath:
                parts = xpath.split("~")
                attribute = parts[1].split("@")[0]
                supported = parts[1].split("@")[1].split(" ")
                xpath = parts[0] + f"//*[@{attribute}]"
                # xpath = parts[0] + "//*[@class and not(" + " or ".join([f"contains(concat(' ', normalize-space(@class), ' '), \" {i} \")" for i in parts[1].split(" ")]) + ")]"
                pc = True
            xpath = re.sub(r"has-class\((\".*?\")\)", "contains(concat(' ', normalize-space(@class), ' '), \\1)", xpath)
            print(xpath)
            print(attribute)
            print(supported)
            file = open("test.html", "w")
            # onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
            onlyfiles = list(manifest.keys())
            fl = 0
            for i in onlyfiles:
                co = False
                for jj in ignore:
                    try:
                        if re.match(jj, manifest[i]):
                            co = True
                            break
                    except Exception:
                        print(i + " failed to find in manifest")
                        co = True
                if co:
                    fl += 1
                    continue

                z = open(mypath + i + ".html", "r", encoding="utf-8")
                z.seek(0)
                try:
                    tree = html.fromstring(z.read().encode("utf8"))
                    results = tree.xpath(xpath)
                    if len(results) > 0:
                        size = shutil.get_terminal_size((80, 20)).columns
                        fm = True
                        for zz in tree.xpath(xpath):
                            if pc:
                                ss = zz.xpath("@" + attribute)[0]
                                if ss == " " or ss == "":
                                    continue
                                split = ss.split(" ")
                                co = False
                                # print("NEW " + ss)
                                for j in split:
                                    # print(j)
                                    for ij in supported:
                                        if ij == " " or ij == "":
                                            continue
                                        # print("supported? " + ij)
                                        if ij.startswith("/") and ij.endswith("/"):
                                            if re.match(ij[1:-1], j):
                                                co = True
                                                break
                                        elif ij in j:
                                            # print("found, drop " + ij)
                                            co = True
                                            break
                                    if co:
                                        break
                                if co:
                                    continue
                            else:
                                try:
                                    ss = etree.tostring(zz, pretty_print=True).decode("utf8")
                                except Exception:
                                    ss = tree.xpath(re.sub(r"(.*)(/@.*)", "name(\\1\\2)", xpath + f"[.=\"{zz}\"]"))
                            if fm:
                                fm = False
                                print(Back.LIGHTGREEN_EX + Fore.BLACK + centerText(f"--- START {manifest[i]} ---") + Style.RESET_ALL)
                                file.write(manifest[i] + "\n")
                            file.write(ss + "\n")
                            file.write("-" * 10 + "\n")
                            print(ss)
                            print(Back.BLACK + Fore.RED + "-" * size + Style.RESET_ALL)
                        if not fm:
                            print(Back.RED + Fore.WHITE + centerText(f"--- END {manifest[i]} ---") + Style.RESET_ALL)
                except Exception as ex:
                    print(ex)
                    pass
                z.close()
                fl += 1
                ctypes.windll.kernel32.SetConsoleTitleW(f"Progress: {fl/len(onlyfiles)*100}% [{fl}/{len(onlyfiles)}]")
            file.close()
            print(Back.LIGHTCYAN_EX + Fore.BLACK + "\n" + centerText("< -- FINISHED -- >") + Style.RESET_ALL)
        except KeyboardInterrupt:
            print(Back.LIGHTCYAN_EX + Fore.BLACK + "\n" + centerText("< -- FORCE FINISHED -- >") + Style.RESET_ALL)
            file.close()

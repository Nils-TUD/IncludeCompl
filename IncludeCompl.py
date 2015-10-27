import sublime, sublime_plugin
import re, os

class IncludeCompletion(sublime_plugin.EventListener):
    def __init__(self):
        self.incl_regex = re.compile(r'^\s*#\s*include\s+(<|")(.*?)(>|")?$')

    def is_source_file(self, name):
        return name.endswith(".c") or name.endswith(".cpp") or name.endswith(".cxx") or \
               name.endswith(".cc") or name.endswith(".S")

    def is_include_file(self, name):
        return name.endswith(".h") or name.endswith(".hh") or name.endswith(".hpp") or \
               name.endswith(".hxx")

    def is_enabled(self, view):
        file = view.file_name()
        return self.is_source_file(file) or self.is_include_file(file)

    def get_include_paths(self, view):
        settings = sublime.load_settings("IncludeCompl.sublime-settings")
        options = settings.get("include_options", [])
        paths = []
        for o in options:
            paths += self.get_include_paths_in(view.settings().get(o))
        return paths

    def get_include_paths_in(self, options):
        res = []
        if options:
            for opt in options:
                if opt[0:2] == "-I":
                    res.append(opt[2:])
        return res

    def get_base(self, inc):
        inc = inc.lower()
        slash = inc.rfind('/')
        if slash != -1:
            return (inc[:slash], inc[slash + 1:])
        return ("", inc)

    def get_files_in(self, path, prefix, closeChar):
        res = []
        try:
            for file in os.listdir(path):
                if file.lower().startswith(prefix):
                    full = os.path.join(path,file)
                    # append "/" for dirs and >|" for files
                    if os.path.isfile(full) and self.is_include_file(file):
                        res.append((file, file + closeChar))
                    elif os.path.isdir(full):
                        res.append((file, file + "/"))
        except:
            pass
        return res

    def on_query_completions(self, view, prefix, locations):
        # multiple cursors not supported
        if not self.is_enabled(view) or len(locations) != 1:
            return []

        # does the line contain an include?
        line = view.line(locations[0])
        linetext = view.substr(sublime.Region(line.a, locations[0]))
        res = self.incl_regex.match(linetext)
        if not res:
            return []

        # get paths
        paths = self.get_include_paths(view) + [os.path.dirname(view.file_name())]
        base = self.get_base(res.group(2))
        closeChar = ">" if res.group(1) == "<" else "\""

        # build completions
        compl = []
        for p in paths:
            compl += self.get_files_in(os.path.join(p,base[0]), base[1], closeChar)
        return compl

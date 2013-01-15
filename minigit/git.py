
from minigit.util import *
from mimetypes import guess_type
from os.path import join, split, splitext
from fnmatch import *

class GitBlob(object):
    is_tree = False
    is_blob = True
    _content = None
    _type = None
    _path = None
    _size = None

    def __init__(self, ref, name, tree):
        self.ref = ref
        self.name = name
        self.tree = tree

    @property
    def content(self):
        if not self._content:
            self._content = run('cd "%s" && git cat-file -p "%s"' % (self.tree.git.path, self.ref))

        return self._content

    @property
    def path(self):
        if not self._path:
            self._path = join(self.tree.path, self.name)
        return self._path

    @property
    def mimetype(self):
        t = guess_type(self.path)
        return t[0] or "application/octet-stream"

    @property
    def extension(self):
        return splitext(self.name)[1][1:].lower()

    @property
    def type(self):
        if not self._type:
            IMAGE_TYPES = ("png", "jpg", "jpeg", "tga", "gif", "bmp")

            if self.extension in IMAGE_TYPES:
                self._type = "image"
            elif self.content == "":
                self._type = "empty"
            elif self.mimetype and self.mimetype.split("/")[0] == "text":
                self._type = "text"
            else:
                try:
                    #self._content = self.content.decode("utf-8", "replace")
                    self._content = self.content
                    self._type = "text"
                except UnicodeDecodeError as e:
                    print e
                    self._type = "unknown"
        return self._type

    @property
    def size(self):
        if not self._size:
            self._size = run('cd "%s" && git cat-file -s "%s"' % (self.tree.git.path, self.ref))
            if not self._size or "fatal" in self._size:
                raise Exception("Could not read file size of '%s' (in %s)" % (self.ref, self.tree.git.path))
        return self._size

class GitTree(object):
    is_tree = True
    is_blob = False
    _children = None
    _path = None
    type = "folder"

    def __init__(self, ref, name, git, parent = None):
        self.ref = ref
        self.git = git
        self.name = name
        self.parent = parent

    @property
    def children(self):
        if not self._children:
            raw = run('cd "%s" && git cat-file -p "%s^{tree}"' % (self.git.path, self.ref))

            if not raw or "fatal" in raw:
                raise Exception("Could not read children of '%s' (in %s)" % (self.ref, self.git.path))

            self._children = []
            for line in raw.splitlines():
                mode, type, ref, name = line.split(None, 3)
                if type == "blob":
                    self._children.append(GitBlob(ref, name, self))
                elif type == "tree":
                    self._children.append(GitTree(ref, name, self.git, self))
                else:
                    if app.debug: print "Invalid type in GitTree.children: %s for %s - %s" % (type, self.name, self.ref)

            # sort the children by name, trees on top
            def sorter(a, b):
                if a.is_tree and not b.is_tree: return -1
                if b.is_tree and not a.is_tree: return 1
                return a.name < b.name

            self._children.sort(sorter)
        return self._children

    @property
    def path(self):
        if not self._path:
            self._path = join(self.parent.path, self.name) if (self.parent and self.parent.name) else self.name
        return self._path

    def find(self, path):
        if type(path) == str or type(path) == unicode:
            _path = path.split("/")
            path = []
            for p in _path:
                if p: path.append(p)

        if len(path) == 0:
            return self

        for c in self.children:
            if fnmatch(c.name, path[0]):
                if type(c) == GitBlob:
                    return c
                m = c.find(path[1:])
                if m:
                    return m

        return None


class GitCommit(object):
    _parents = None
    _tree = None
    _author = None
    _committer = None

    def __init__(self, ref, git):
        self.ref = ref
        self.git = git

        self.tree_ref = ""
        self.parent_refs = []
        self.author_raw = ""
        self.committer_raw = ""
        self.message = ""

        self.read()

    @property
    def parents(self):
        if not self._parents:
            self._parents = []
            for parent_ref in self.parent_refs:
                self._parents.append(GitCommit(parent_ref, self.git))
        return self._parents

    @property
    def author(self):
        if not self._author:
            self._author = get_email_user(extract_email(self.author_raw))
        return self._author

    @property
    def committer(self):
        if not self._committer:
            self._committer = get_email_user(extract_email(self.committer_raw))
        return self._committer

    @property
    def tree(self):
        if not self._tree:
            self._tree = self.git.getTree(self.tree_ref)
        return self._tree

    def read(self):
        """ A typical output might look like this:
        tree 8a59ea030d1617d624b473d1e66126826373f07c
        parent 2d4125b8ac6192dad199faaeeec24969e648ed11
        parent d2694b42fca4c2efe55ba2734d09ff7aa7fa8e0e
        author Firstname Lastname <mail@example.com> 1334605655 +0200
        committer Firstname Lastname <mail@example.com> 1334605655 +0200

        This is the commit message. It will go down to the last
        lines of the output. There is a newline at the end. Strip it.
        """
        raw = run('cd "%s" && git cat-file -p "%s"' % (self.git.path, self.ref))

        if not raw or "fatal" in raw:
            raise Exception("Commit not found: '%s' (in %s)" % (self.ref, self.git.path))

        is_message = False
        for line in raw.splitlines():
            line = line.strip()
            if not is_message:
                if line == "":
                    is_message = True
                else:
                    split = line.split(" ", 1)
                    if split[0] == "tree":
                        self.tree_ref = split[1]
                    if split[0] == "parent":
                        self.parent_refs.append(split[1])
                    if split[0] == "author":
                        self.author_raw = split[1]
                        self.author_time = parse_date(self.author_raw[-16:])
                    if split[0] == "committer":
                        self.committer_raw = split[1]
                        self.commit_time = parse_date(self.committer_raw[-16:])

            else:
                self.message += line.strip() + "\n"

        if not self.author_raw: self.author_raw = self.committer_raw
        if not self.author_time: self.author_time = self.commit_time

class Git(object):
    _branches = None
    _commit_cache = {}

    def __init__(self, path):
        self.path = path

    def getTree(self, ref):
        return GitTree(ref, "", self, None)

    def getCommit(self, ref):
        if not ref in self._commit_cache.keys():
            self._commit_cache[ref] = GitCommit(ref, self)
        return self._commit_cache[ref]

    def getCommits(self, ref = "master"):
        try:
            raw = run('cd "%s" && git log "%s" --oneline --abbrev=40 --' % (self.path, ref))

            if not raw or "fatal" in raw:
                raise Exception("Could not read commit log from ref '%s' (in %s)" % (ref, self.path))

            commits = []
            for line in raw.splitlines():
                commits.append(self.getCommit(line[:40]))
            return commits
        except:
            return []

    def isBranch(self, ref):
        ref = self.refHash(ref)
        for b in self.branches:
            if self.refHash(b) == ref:
                return True
        return False

    def getNodeHistory(self, path):
        raw = run('cd "%s" && git log --oneline --abbrev=40 -- "%s"' % (self.path, path))

        if not raw or "fatal" in raw:
            raise Exception("Could not get node history of %s (in %s)" % (path, self.path))

        commits = []
        for line in raw.splitlines():
            commits.append(self.getCommit(line[:40]))
        return commits

    def lastChangedCommit(self, ref, path):
        h = self.getNodeHistory(path)
        c = self.getCommit(ref)
        if not c:
            raise Exception("Could not find commit '%s'" % ref)
        while len(h) > 1 and h[0].author_time > c.author_time:
            h = h[1:]

        return h[0] if h else None

    @property
    def branches(self):
        if not self._branches:
            self._branches = []
            raw = run('cd "%s" && git branch' % self.path)

            if "fatal" in raw:
                raise Exception("Could not fetch branch list (in %s)" % self.path)

            for line in raw.splitlines():
                if line[0] == "*": line = line[1:]
                line = line.strip()
                self._branches.append(line)
        return self._branches

    def refHash(self, ref):
        raw = run('cd "%s" && git rev-parse "%s"' % (self.path, ref))

        if not raw or "fatal" in raw:
            raise Exception("Could not parse hash of ref '%s' (in %s)" % (ref, self.path))

        return raw.strip()



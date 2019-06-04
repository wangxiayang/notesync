from evernote.api.client import EvernoteClient
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types

import os

from config import auth_token, local_store_path, notebook_name

client = EvernoteClient(token=auth_token, sandbox=False, china=False)
note_store = client.get_note_store()

notebooks = note_store.listNotebooks()
for n in notebooks:
    if n.name == notebook_name:
        nb_guid = n.guid

nf = NoteStore.NoteFilter(
        notebookGuid=nb_guid)
spec = NoteStore.NotesMetadataResultSpec(
        includeTitle=True)
nml = note_store.findNotesMetadata(auth_token,
        nf,
        0,
        100,
        spec)

for nm in nml.notes:
    n = note_store.getNote(auth_token,
            nm.guid,
            True,
            True,
            True,
            True)

    # a file is not a file
    dir_path = local_store_path + "/enml/" + notebook_name + "/" + n.guid
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    # timestamp
    if not os.path.exists(dir_path + "/updated"):
        f = open(dir_path + "/updated", "w+")
        f.write(str(n.updated))
        f.close()
        need_sync = True
    else:
        f = open(dir_path + "/updated", "rw")
        ts_local = int(f.read())
        if ts_local == n.updated:
            need_sync = False
        else:
            assert ts_local < n.updated
            need_sync = True
            f.write(str(n.updated))
            f.close()

    if need_sync:
        print "sync " + n.title
        # title
        f = open(dir_path + "/title", "w+")
        f.write(n.title)
        f.close()

        # content
        f = open(dir_path + "/content", "w+")
        f.write(n.content.encode('utf-8'))
        f.close()

        # generate md
        f = open(dir_path + "/content", "r")
        assert f.readline() == "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"
        assert f.readline() == "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n"
        assert f.readline() == "<en-note>\n"

        md_path = local_store_path + "/md/" + notebook_name + "/" + n.guid
        if not os.path.isdir(md_path):
            os.mkdir(md_path)

        fout = open(md_path + "/content.md", "w+")

        l = f.readline()
        while l != "</en-note>\n":
            fout.write(l)
            l = f.readline()
        fout.close()

        fout = open(md_path + "/title", "w+")
        fout.write(n.title)
        fout.close()

        fout = open(md_path + "/updated", "w+")
        fout.write(str(n.updated))
        fout.close()

    else:
        print "no need to sync " + n.title

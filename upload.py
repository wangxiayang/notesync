from evernote.api.client import EvernoteClient
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types

import os
import time

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
    dir_root = local_store_path + "/enml/" + notebook_name
    dir_path = dir_root + "/" + n.guid
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

    assert not need_sync

md_root = local_store_path + "/md/" + notebook_name
for note in os.listdir(md_root):
    md_path = md_root + "/" + note
    if not note.startswith("newnote"):
        assert os.path.isfile(md_path + "/updated")
        f = open(md_path + "/updated", "r")
        ts = int(f.read())
        f.close()

        if ts != -1:
            continue

    assert os.path.isfile(md_path + "/content.md")
    assert os.path.isfile(md_path + "/title")

    f = open(md_path + "/content.md", "r")
    content = f.read()
    f.close()

    f = open(md_path + "/title", "r")
    title = f.read()
    title = title[0:-1]
    f.close()

    print "... in sync " + title

    if note.startswith("newnote"):
        enote = Types.Note()
    else:
        enote = note_store.getNote(auth_token,
                note,
                False,
                False,
                False,
                False)
        enote.updated = int(time.time() * 1000)

    enote.title = title
    enote.notebookGuid = nb_guid
    enote.content = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n"
    enote.content += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">\n"
    enote.content += "<en-note>\n"
    enote.content += content.encode('utf-8')
    enote.content += "</en-note>\n"

    if note.startswith("newnote"):
        created_note = note_store.createNote(enote)
    else:
        created_note = note_store.updateNote(enote)

    dir_path = dir_root + "/" + created_note.guid

    if note.startswith("newnote"):
        os.mkdir(dir_path)

    # enml-title
    f = open(dir_path + "/title", "w+")
    f.write(title)
    f.close()

    # enml-content
    f = open(dir_path + "/content", "w+")
    f.write(enote.content)
    f.close()

    # enml-timestamp
    f = open(dir_path + "/updated", "w+")
    f.write(str(created_note.updated))
    f.close()

    f = open(md_path + "/updated", "w+")
    f.write(str(created_note.updated))
    f.close()

    if note.startswith("newnote"):
        os.rename(md_path, md_root + "/" + created_note.guid)

    print "done sync " + title

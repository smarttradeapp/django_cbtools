// deleted documents
// see `manage.py clear_deleted` to investigate about the usage
// in short words we really delete things in a month
function (doc, meta) {
    // no need to index Sync-Gateway documents
    if (meta.id.substring(0, 5) == "_sync") {
        return;
    }

    if (doc.st_deleted) {
        var dt = '0000-00-00';
        if (doc.updated) {
            dt = doc.updated.substring(0, 10);
        }
        emit(dt, null);
    }
}

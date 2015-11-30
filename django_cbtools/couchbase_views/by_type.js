function (doc, meta) {
    // no need to index Sync-Gateway documents
    if (meta.id.substring(0, 5) == "_sync") {
        return;
    }

    if (doc.st_deleted) {
        return;
    }

    emit(doc.doc_type, null);
}
function (doc, meta) {
    // no need to index Sync-Gateway documents
    if (meta.id.substring(0, 5) == "_sync") {
        return;
    }

    if (doc.st_deleted) {
        return;
    }

    for (channel in doc.channels) {
        emit([doc.channels[channel], doc.doc_type], null)
    }
}

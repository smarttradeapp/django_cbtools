function (doc, meta) {
    if (doc.st_deleted) {
        return;
    }
    for (channel in doc.channels) {
        emit([doc.channels[channel], doc.doc_type], null)
    }
}

function (doc, meta) {
    if (doc.st_deleted) {
        return;
    }
    emit(doc.doc_type, null);
}
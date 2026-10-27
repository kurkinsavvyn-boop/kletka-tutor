/// <reference path="../pb_data/types.d.ts" />
// «Мои материалы»: свои файлы репетитора (PDF, картинки, документы). Видит и меняет только владелец.
migrate((app) => {
  const users = app.findCollectionByNameOrId("users")
  const files = new Collection({
    type: "base",
    name: "files",
    listRule: "owner = @request.auth.id",
    viewRule: "owner = @request.auth.id",
    createRule: "@request.auth.collectionName = 'users' && owner = @request.auth.id",
    updateRule: "owner = @request.auth.id && (@request.body.owner:isset = false || @request.body.owner = @request.auth.id)",
    deleteRule: "owner = @request.auth.id",
    fields: [
      { type: "relation", name: "owner", collectionId: users.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "file", name: "file", required: true, maxSelect: 1, maxSize: 25000000, protected: true },
      { type: "text", name: "name", max: 200 },
      { type: "text", name: "folder", max: 80 },
      { type: "autodate", name: "created", onCreate: true },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE INDEX idx_files_owner ON files (owner)"],
  })
  app.save(files)
}, (app) => {
  try { app.delete(app.findCollectionByNameOrId("files")) } catch (e) {}
})

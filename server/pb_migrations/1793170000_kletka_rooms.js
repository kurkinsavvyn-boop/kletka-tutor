/// <reference path="../pb_data/types.d.ts" />
// Комната урока: одна на ученика, навсегда (тетрадь).
//   rooms  — материалы и состояние урока (пишет репетитор), ответы ученика (пишет ученик), копии файлов;
//   pulse  — быстрое и мелкое: где каждый сейчас, указка, кто печатает. По одной записи на репетитора и ученика;
//   ink    — линии маркера на страницах материалов.
// Видят комнату только её репетитор и её ученик.
migrate((app) => {
  const users = app.findCollectionByNameOrId("users")
  const students = app.findCollectionByNameOrId("students")

  const rooms = new Collection({
    type: "base",
    name: "rooms",
    listRule: "tutor = @request.auth.id || student = @request.auth.id",
    viewRule: "tutor = @request.auth.id || student = @request.auth.id",
    createRule: "@request.auth.collectionName = 'users' && tutor = @request.auth.id && student.tutor = @request.auth.id",
    // ученик меняет только свои ответы
    updateRule: "tutor = @request.auth.id || (student = @request.auth.id && @request.body.mats:isset = false && @request.body.st:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.docs:isset = false)",
    deleteRule: "tutor = @request.auth.id",
    fields: [
      { type: "relation", name: "tutor", collectionId: users.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "relation", name: "student", collectionId: students.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "json", name: "mats", maxSize: 2000000 },
      { type: "json", name: "st", maxSize: 200000 },
      { type: "json", name: "ans", maxSize: 2000000 },
      { type: "file", name: "docs", maxSelect: 999, maxSize: 25000000, protected: true },
      { type: "autodate", name: "created", onCreate: true },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE UNIQUE INDEX idx_rooms_student ON rooms (student)", "CREATE INDEX idx_rooms_tutor ON rooms (tutor)"],
  })
  app.save(rooms)

  const mine = "room.tutor = @request.auth.id || room.student = @request.auth.id"
  const asSelf = "(room.tutor = @request.auth.id && who = 't') || (room.student = @request.auth.id && who = 's')"

  const pulse = new Collection({
    type: "base",
    name: "pulse",
    listRule: mine,
    viewRule: mine,
    createRule: asSelf,
    updateRule: asSelf + " && (@request.body.who:isset = false) && (@request.body.room:isset = false)",
    deleteRule: "room.tutor = @request.auth.id",
    fields: [
      { type: "relation", name: "room", collectionId: rooms.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "text", name: "who", required: true, max: 1, pattern: "^[ts]$" },
      { type: "json", name: "d", maxSize: 20000 },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE UNIQUE INDEX idx_pulse_room_who ON pulse (room, who)"],
  })
  app.save(pulse)

  const ink = new Collection({
    type: "base",
    name: "ink",
    listRule: mine,
    viewRule: mine,
    createRule: asSelf,
    updateRule: null,
    deleteRule: "room.tutor = @request.auth.id || (room.student = @request.auth.id && who = 's')",
    fields: [
      { type: "relation", name: "room", collectionId: rooms.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "text", name: "mat", required: true, max: 40 },
      { type: "number", name: "pg" },
      { type: "text", name: "who", required: true, max: 1, pattern: "^[ts]$" },
      { type: "text", name: "kind", max: 10 },
      { type: "json", name: "pts", maxSize: 200000 },
      { type: "autodate", name: "created", onCreate: true },
    ],
    indexes: ["CREATE INDEX idx_ink_room ON ink (room, mat)"],
  })
  app.save(ink)
}, (app) => {
  for (const n of ["ink", "pulse", "rooms"]) {
    try { app.delete(app.findCollectionByNameOrId(n)) } catch (e) {}
  }
})

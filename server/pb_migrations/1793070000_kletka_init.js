/// <reference path="../pb_data/types.d.ts" />
// Схема «Клетки»:
//   users        — репетиторы (встроенная коллекция входа PocketBase);
//   workspaces   — рабочая среда репетитора целиком (ученики, работы, свои темы), одна запись на репетитора;
//   students     — аккаунты учеников для входа по логину и паролю, каждый привязан к своему репетитору;
//   assignments  — домашки, отправленные ученику в кабинет, и их результаты.
// Каждый видит только своё: правила доступа сверяют владельца с тем, кто вошёл.
migrate((app) => {
  const users = app.findCollectionByNameOrId("users")

  const workspaces = new Collection({
    type: "base",
    name: "workspaces",
    listRule: "owner = @request.auth.id",
    viewRule: "owner = @request.auth.id",
    createRule: "@request.auth.collectionName = 'users' && owner = @request.auth.id",
    updateRule: "owner = @request.auth.id && (@request.body.owner:isset = false || @request.body.owner = @request.auth.id)",
    deleteRule: "owner = @request.auth.id",
    fields: [
      { type: "relation", name: "owner", collectionId: users.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "json", name: "data", maxSize: 8000000 },
      { type: "autodate", name: "created", onCreate: true },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE UNIQUE INDEX idx_workspaces_owner ON workspaces (owner)"],
  })
  app.save(workspaces)

  const students = new Collection({
    type: "auth",
    name: "students",
    listRule: "id = @request.auth.id || tutor = @request.auth.id",
    viewRule: "id = @request.auth.id || tutor = @request.auth.id",
    createRule: "@request.auth.collectionName = 'users' && tutor = @request.auth.id",
    updateRule: "tutor = @request.auth.id && (@request.body.tutor:isset = false || @request.body.tutor = @request.auth.id)",
    deleteRule: "tutor = @request.auth.id",
    // репетитор может сменить ученику пароль без старого пароля
    manageRule: "tutor = @request.auth.id",
    fields: [
      { type: "relation", name: "tutor", collectionId: users.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "text", name: "login", required: true, min: 3, max: 40, pattern: "^[a-z0-9-]+$" },
      { type: "text", name: "name", max: 80 },
      { type: "text", name: "surname", max: 80 },
      { type: "text", name: "tutorName", max: 120 },
      { type: "number", name: "grade" },
      { type: "text", name: "localId", max: 40 },
      { type: "autodate", name: "created", onCreate: true },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE UNIQUE INDEX idx_students_login ON students (login)"],
    passwordAuth: { enabled: true, identityFields: ["login"] },
  })
  app.save(students)
  // у ученика нет почты: вход только по логину и короткому паролю из 6 цифр
  const st = app.findCollectionByNameOrId("students")
  st.fields.getByName("email").required = false
  st.fields.getByName("password").min = 6
  app.save(st)

  const assignments = new Collection({
    type: "base",
    name: "assignments",
    listRule: "tutor = @request.auth.id || student = @request.auth.id",
    viewRule: "tutor = @request.auth.id || student = @request.auth.id",
    createRule: "@request.auth.collectionName = 'users' && tutor = @request.auth.id && student.tutor = @request.auth.id",
    // ученик может только сдать работу: менять статус и результат
    updateRule: "tutor = @request.auth.id || (student = @request.auth.id && @request.body.payload:isset = false && @request.body.tutor:isset = false && @request.body.student:isset = false && @request.body.code:isset = false)",
    deleteRule: "tutor = @request.auth.id",
    fields: [
      { type: "relation", name: "tutor", collectionId: users.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "relation", name: "student", collectionId: students.id, required: true, maxSelect: 1, cascadeDelete: true },
      { type: "text", name: "code", required: true, max: 40 },
      { type: "text", name: "title", max: 200 },
      { type: "json", name: "payload", maxSize: 200000 },
      { type: "select", name: "status", values: ["issued", "done"], maxSelect: 1 },
      { type: "json", name: "result", maxSize: 200000 },
      { type: "autodate", name: "created", onCreate: true },
      { type: "autodate", name: "updated", onCreate: true, onUpdate: true },
    ],
    indexes: ["CREATE INDEX idx_assignments_student ON assignments (student)", "CREATE INDEX idx_assignments_tutor ON assignments (tutor)"],
  })
  app.save(assignments)
}, (app) => {
  for (const n of ["assignments", "students", "workspaces"]) {
    try { app.delete(app.findCollectionByNameOrId(n)) } catch (e) {}
  }
})

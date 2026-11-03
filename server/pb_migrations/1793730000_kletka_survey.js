/// <reference path="../pb_data/types.d.ts" />
// Опрос репетиторов (kletka-tutor/opros/): отправить может любой без входа, читать — только администратор.
migrate((app) => {
  const survey = new Collection({
    type: "base",
    name: "survey",
    listRule: null,
    viewRule: null,
    createRule: "",
    updateRule: null,
    deleteRule: null,
    fields: [
      { type: "text", name: "name", max: 200 },
      { type: "json", name: "answers", maxSize: 200000 },
      { type: "text", name: "text", max: 100000 },
      { type: "autodate", name: "created", onCreate: true },
    ],
  })
  app.save(survey)
}, (app) => {
  try { app.delete(app.findCollectionByNameOrId("survey")) } catch (e) {}
})

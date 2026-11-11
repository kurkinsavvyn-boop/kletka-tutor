/// <reference path="../pb_data/types.d.ts" />
// Лимиты файлов, 11.11.2026.
//   Комната: до 3000 файлов (страницы PDF, картинки, перенесённые картинки разработок), каждый до 100 МБ.
//   Мои материалы: файл до 100 МБ (учебник в PDF).
//   Список материалов комнаты (mats): до 5 МБ, большие разработки из Miro туда не помещались.
const MB = 1024 * 1024

function set(app, col, field, patch) {
  const c = app.findCollectionByNameOrId(col)
  const f = c.fields.getByName(field)
  if (!f) return
  Object.assign(f, patch)
  app.save(c)
}

migrate((app) => {
  set(app, "rooms", "docs", { maxSelect: 3000, maxSize: 100 * MB })
  set(app, "rooms", "mats", { maxSize: 5 * MB })
  set(app, "files", "file", { maxSize: 100 * MB })
}, (app) => {
  set(app, "rooms", "docs", { maxSelect: 999, maxSize: 25 * MB })
  set(app, "rooms", "mats", { maxSize: 2 * MB })
  set(app, "files", "file", { maxSize: 25 * MB })
})

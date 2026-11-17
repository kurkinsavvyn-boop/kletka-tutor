/// <reference path="../pb_data/types.d.ts" />
// 17.11.2026. Ученик открывает картинки разработок своего репетитора напрямую.
// Раньше компьютер репетитора на уроке скачивал каждую картинку и заново загружал её в комнату: большая доска грузилась у ученика минутами,
// а поток загрузок упирался в ограничение сервера («Нет связи»). Список файлов ученику по-прежнему не виден: только файл по точной ссылке.
migrate((app) => {
  const c = app.findCollectionByNameOrId("files")
  c.viewRule = "owner = @request.auth.id || (@request.auth.collectionName = 'students' && @request.auth.tutor = owner)"
  app.save(c)
}, (app) => {
  const c = app.findCollectionByNameOrId("files")
  c.viewRule = "owner = @request.auth.id"
  app.save(c)
})

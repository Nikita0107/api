from tasks import extract_text_from_image
from database import new_session, Document, DocumentText
from fastapi import HTTPException, File, UploadFile, APIRouter
from datetime import datetime, timezone
import shutil
import os
import uuid
import sqlalchemy as sa
from schemas import DocumentResponse, DocumentTextsResponse, DocumentTextResponse

router = APIRouter()

# Каталог для хранения загруженных документов
DOCUMENTS_DIR = "documents"
os.makedirs(DOCUMENTS_DIR, exist_ok=True)


@router.post('/upload_doc', response_model=DocumentResponse, summary="Загрузить картинку",
             description="Загрузите картинку с текстом на сервер. Размер должен быть меньше 2 МБ")
async def document_upload(file: UploadFile = File(...)):
    file.file.seek(0, 2)  # Перемещаем указатель в конец файла
    file_size = file.file.tell()  # Получаем размер файла
    await file.seek(0)  # Возвращаем указатель в начало файла
    if file_size > 2 * 1024 * 1024:  # Проверяем размер файла
        raise HTTPException(status_code=400, detail='большой размер файла')

    unique_filename = f'{uuid.uuid4()}.{file.filename.split(".")[-1]}'  # Генерируем уникальное имя файла

    async with new_session() as session:  # Создаем новую сессию в базе данных
        async with session.begin():  # Начинаем транзакцию
            document = Document(name=unique_filename, date=datetime.now(timezone.utc))  # Создаем новый документ
            session.add(document)  # Добавляем документ в сессию
            await session.flush()  # Записываем изменения в базу данных

            file_path = os.path.join(DOCUMENTS_DIR, unique_filename)  # Полный путь к файлу

            with open(file_path, 'wb') as buffer:  # Открываем файл для записи
                shutil.copyfileobj(file.file, buffer)  # Копируем содержимое файла в буфер

            await session.commit()  # Завершаем транзакцию

    return document


@router.delete("/doc_delete/{doc_id}", summary="Удалить документ",
               description="Удалить документ и связанные с ним текстовые записи из базы данных..")
async def delete_doc(doc_id: int):
    async with new_session() as session:
        try:
            async with session.begin():
                # Находим документ по ID
                document = await session.get(Document, doc_id)
                if not document:
                    raise HTTPException(status_code=404, detail="Документ не найден")
                # Удаляем файл с диска
                file_path = os.path.join(DOCUMENTS_DIR, document.name)
                if os.path.exists(file_path):
                    os.remove(file_path)

                # Удаляем запись из таблицы DocumentText
                await session.execute(sa.delete(DocumentText).where(DocumentText.document_id == doc_id))

            await session.commit()  # Завершаем транзакцию

        except Exception as e:
            await session.rollback()  # Откатываем транзакцию в случае ошибки
            raise HTTPException(status_code=500, detail=str(e))

        # Удаляем запись из таблицы Document
        await session.delete(document)
        await session.commit()

        return {"Сообщение": "документ удален"}


@router.post("/doc_analyse/{doc_id}", summary="Анализ документа",
             description="Запустить анализ извлечения текста в указанном документе.")
async def analyze_doc(doc_id: int):
    async with new_session() as session:
        document = await session.get(Document, doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Документ не найден")

    file_path = os.path.join(DOCUMENTS_DIR, document.name)
    extract_text_from_image.delay(doc_id, file_path)  # Извлечение текста из изображения с использованием Celery

    return {"message": "Анализ начат"}


@router.get('/get_text/{doc_id}', response_model=DocumentTextsResponse, summary='Получить извлеченный текст',
            description="Получить извлеченный текст, связанный с указанным документом.")
async def get_text(doc_id: int):
    async with new_session() as session:
        document_texts = await session.execute(
            sa.select(DocumentText).where(DocumentText.document_id == doc_id)
        )
        texts = document_texts.scalars().all()

        if not texts:
            raise HTTPException(status_code=404, detail="Текст для этого документа не найден")

    return DocumentTextsResponse(
        document_id=doc_id,
        texts=[DocumentTextResponse.model_validate(text) for text in texts]
    )

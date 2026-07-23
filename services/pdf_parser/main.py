from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from parser import parse_sgk_pdf_bytes

app = FastAPI(
    title="SGK PDF Parser Service",
    description="e-Devlet SGK Hizmet Dökümü PDF Ayıklama Servisi",
    version="1.0.0",
)

# Mobil ve Web uygulamalarının bağlanabilmesi için CORS izni
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "online", "service": "SGK PDF Parser"}


@app.post("/parse-pdf")
async def parse_pdf_endpoint(file: UploadFile = File(...)):
    """Kullanıcının yüklediği PDF dosyasını alır ve ayrıştırılmış veriyi döner."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Lütfen geçerli bir PDF dosyası yükleyin."
        )

    try:
        pdf_bytes = await file.read()
        result = parse_sgk_pdf_bytes(pdf_bytes)

        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["error"])

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"PDF işlenirken hata oluştu: {str(e)}"
        )
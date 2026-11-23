"""Export router: Professional JSON, CSV, Printable PDF, and Swatch Sheet PNG exports."""
from fastapi import APIRouter, Response, HTTPException, status
from models.schemas import PaletteConcept
from modules.export_service import (
    export_palette_json,
    export_palette_csv,
    generate_swatch_sheet_png,
    generate_pdf_report
)

router = APIRouter(prefix="/export", tags=["Exports & Reports"])


@router.post("/json")
def export_json(palette: PaletteConcept):
    """Export palette specification as formatted JSON."""
    content = export_palette_json(palette)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={palette.id}_palette.json"}
    )


@router.post("/csv")
def export_csv(palette: PaletteConcept):
    """Export palette specification as CSV."""
    content = export_palette_csv(palette)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={palette.id}_palette.csv"}
    )


@router.post("/pdf")
def export_pdf(palette: PaletteConcept):
    """Export printable architectural specification PDF sheet."""
    try:
        buf = generate_pdf_report(palette)
        return Response(
            content=buf.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={palette.id}_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {str(e)}")


@router.post("/png")
def export_png(palette: PaletteConcept):
    """Export swatch palette sheet as high-resolution PNG graphic."""
    try:
        buf = generate_swatch_sheet_png(palette)
        return Response(
            content=buf.getvalue(),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={palette.id}_swatches.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PNG generation failed: {str(e)}")

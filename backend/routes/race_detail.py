from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin", tags=["admin-ui"])


@router.get("/race/{race_id}", response_class=HTMLResponse)
def race_detail_page(race_id: str):
    return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <title>경주 상세 - {race_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
        }}
        h1 {{
            margin-bottom: 10px;
        }}
        .box {{
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
        }}
        .label {{
            font-weight: bold;
        }}
        .pass {{
            color: red;
            font-weight: bold;
        }}
        .go {{
            color: green;
            font-weight: bold;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>

<h1>경주 상세</h1>

<div class="box">
    <div><span class="label">Race ID:</span> {race_id}</div>
    <div><span class="label">예측 상태:</span> <span class="go">GO</span></div>
    <div><span class="label">Confidence:</span> 0.73</div>
</div>

<div class="box">
    <h3>말별 점수</h3>
    <table>
        <tr>
            <th>번호</th>
            <th>말 이름</th>
            <th>점수</th>
        </tr>
        <tr>
            <td>1</td>
            <td>Sample Horse A</td>
            <td>0.73</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Sample Horse B</td>
            <td>0.55</td>
        </tr>
        <tr>
            <td>3</td>
            <td>Sample Horse C</td>
            <td>0.41</td>
        </tr>
    </table>
</div>

</body>
</html>
"""

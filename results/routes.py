# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ext import db
from models import PrivacyResult, PrivacyItem, DesensitizationResult  # 这是等会儿你在 models.py 里要加的三张表

bp = Blueprint("results", __name__)

def _ok(data, status=200):
    return jsonify(data), status

def _err(msg, code, status):
    return jsonify({"error": code, "message": msg}), status

def _is_admin():
    # 你的 User 模型里有 has_role 方法
    return hasattr(current_user, "has_role") and current_user.has_role("admin")

def _require_task_owner_or_admin(task_id: int):
    """
    这里先用简化版：因为你的 Task 表不在 models.py 里展示，
    我们默认：只要登录即可，或者将来补上 Task.create_user_id 的校验。
    现在先不阻塞你跑通接口。
    """
    return True

@bp.get("/api/v1/privacy-results/<int:task_id>")
@login_required
def get_privacy_result(task_id: int):
    if not _require_task_owner_or_admin(task_id) and not _is_admin():
        return _err("FORBIDDEN", "FORBIDDEN", 403)
    pr = PrivacyResult.query.filter_by(task_id=task_id).first()
    if not pr:
        return _err("NOT_FOUND", "NOT_FOUND", 404)
    data = {
        "task_id": pr.task_id,
        "source_file": {"id": pr.source_file_id},
        "detected_at": pr.detected_at.isoformat() if pr.detected_at else None,
        "duration_ms": pr.duration_ms,
        "total_hits": pr.total_hits,
        "hits_by_type": pr.hits_by_type or {}
    }
    return _ok(data)

@bp.get("/api/v1/privacy-items")
@login_required
def get_privacy_items():
    result_id = request.args.get("resultId", type=int)
    if not result_id:
        return _err("resultId required", "VALIDATION_FAILED", 400)

    q = PrivacyItem.query.filter_by(result_id=result_id)

    pt = request.args.get("privacyType")
    if pt: q = q.filter(PrivacyItem.privacy_type == pt)

    rl = request.args.get("riskLevel")
    if rl: q = q.filter(PrivacyItem.risk_level == rl)

    minc = request.args.get("minConf", type=float)
    if minc is not None: q = q.filter(PrivacyItem.confidence >= minc)

    maxc = request.args.get("maxConf", type=float)
    if maxc is not None: q = q.filter(PrivacyItem.confidence <= maxc)

    page = max(request.args.get("page", default=1, type=int), 1)
    size = min(max(request.args.get("size", default=20, type=int), 1), 100)

    total = q.count()
    items = (q.order_by(PrivacyItem.row_no.asc())
               .offset((page-1)*size).limit(size).all())

    def to_dict(x: PrivacyItem):
        return {
            "row_no": x.row_no,
            "col_name": x.col_name,
            "privacy_type": x.privacy_type,
            "risk_level": x.risk_level,
            "confidence": float(x.confidence) if x.confidence is not None else None,
            "sample_masked": x.sample_masked
        }

    return _ok({"items": [to_dict(i) for i in items],
                "page": page, "size": size, "total": total})

@bp.get("/api/v1/desensitization-results/<int:task_id>")
@login_required
def get_desens_result(task_id: int):
    if not _require_task_owner_or_admin(task_id) and not _is_admin():
        return _err("FORBIDDEN", "FORBIDDEN", 403)
    dr = DesensitizationResult.query.filter_by(task_id=task_id).first()
    if not dr:
        return _err("NOT_FOUND", "NOT_FOUND", 404)
    data = {
        "task_id": dr.task_id,
        "algorithm": {
            "id": dr.algorithm_id,
            "name": dr.algorithm_name,
            "version": dr.algorithm_version
        },
        "duration_ms": dr.duration_ms,
        "source_input_file": {"id": dr.source_input_file_id},
        "perception_result_file": {"id": dr.perception_result_file_id},
        "desens_output_file": {"id": dr.desens_output_file_id}
    }
    return _ok(data)

@bp.post("/api/v1/privacy-items/export")
@login_required
def post_export():
    body = request.get_json(silent=True) or {}
    result_id = body.get("resultId")
    if not result_id:
        return _err("resultId required", "VALIDATION_FAILED", 400)
    # 真实导出：建议生成一个导出任务并异步产出文件；此处返回占位 ID
    export_task_id = 3001
    return _ok({"export_task_id": export_task_id})

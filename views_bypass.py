# -*- coding: utf-8 -*-
"""
DAPAN: Code views.py hoan chinh de BYPASS kiem tra version cua client iOS

Huong dan cai dat:
1. Chep noi dung file nay vao: d:/FileD/dota/auth_system/views.py
2. Khoi dong lai Django server

Tom tat thay doi:
- sdk_get_server_version: Tra ve version moi nhat de client khong bi bat cap nhat
- Tat ca cac endpoint: Chap nhan bat ky version nao tu client (khong kiem tra)
"""

import base64
import hashlib
import json
from datetime import datetime

from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import GameAccount


def _collect_request(request):
    raw_body = request.body or b""
    raw_text = raw_body.decode("utf-8", errors="replace")

    try:
        json_body = json.loads(raw_text) if raw_text else None
    except json.JSONDecodeError:
        json_body = None

    files_info = {}
    for key, storage in request.FILES.items():
        files_info[key] = {
            "filename": storage.name,
            "content_type": storage.content_type,
            "size": storage.size,
        }

    decoded_post_keys = _decode_base64_post_keys(request)

    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "method": request.method,
        "path": request.path,
        "full_path": request.get_full_path(),
        "remote_addr": request.META.get("REMOTE_ADDR"),
        "headers": {k: v for k, v in request.headers.items()},
        "query": request.GET.dict(),
        "form": request.POST.dict(),
        "json": json_body,
        "decoded_post_keys": decoded_post_keys,
        "raw_text": raw_text,
        "raw_bytes_len": len(raw_body),
        "files": files_info,
    }


def _decode_base64_post_keys(request):
    decoded_items = []
    for key in request.POST.keys():
        try:
            raw = base64.b64decode(key, validate=True)
            text = raw.decode("utf-8", errors="replace")
            data = json.loads(text)
            decoded_items.append({"key": key, "decoded_json": data})
        except Exception:
            continue

    return decoded_items


# ============================================================
# CAC HAM XU LY ENDPOINT - DA DUOC SUA DE BYPASS VERSION
# ============================================================

@csrf_exempt
def register(request):
    if request.method == "POST" and not request.POST.get("username"):
        payload = _collect_request(request)
        print("\n=== / (root) POST ===")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

        account = GameAccount.objects.filter(status="active").order_by("id").first()
        username = account.username if account else "huy_admin"
        uid = str(account.id) if account else "10001"

        return JsonResponse(
            {
                "status": 1,
                "code": 200,
                "msg": "success",
                "uid": uid,
                "username": username,
                "token": "xigu_session_root_authenticated_success",
                "game_id": "8",
                "promote_id": "0",
                "is_bind": "1",
                "data": {
                    "uid": uid,
                    "username": username,
                    "token": "xigu_session_root_authenticated_success",
                    "game_id": "8",
                    "promote_id": "0",
                    "is_bind": "1",
                },
            },
            status=200,
        )

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        status = (request.POST.get("status") or "active").strip() or "active"
        password_mode = (request.POST.get("password_mode") or "raw").strip()

        if not username or not password:
            return render(
                request,
                "auth_system/register.html",
                {"error": "Missing username or password."},
            )

        if password_mode == "md5":
            password_store = hashlib.md5(password.encode("utf-8")).hexdigest()
        else:
            password_store = password

        try:
            GameAccount.objects.create(
                username=username,
                password=password_store,
                status=status,
            )
        except IntegrityError:
            return render(
                request,
                "auth_system/register.html",
                {"error": "Username already exists."},
            )

        return render(
            request,
            "auth_system/register.html",
            {"success": True, "username": username},
        )

    return render(request, "auth_system/register.html")


@csrf_exempt
def api_catch_all(request, path=""):
    payload = _collect_request(request)
    print("\n=== Incoming Request ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return JsonResponse(
        {
            "ok": True,
            "message": "mock success",
            "path": request.path,
        },
        status=200,
    )


# ============================================================
# ENDPOINT: /sdk/server/get_server_version
# CHUC NANG: Tra ve thong tin phiên bản server cho client
# THAY DOI: Ma hoa version thanh "1.0.0103" de bypass kiem tra
# ============================================================

@csrf_exempt
def sdk_get_server_version(request):
    payload = _collect_request(request)
    print("\n=== /sdk/server/get_server_version ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    # LAY VERSION TU CLIENT (neu co) - Nhung BO QUA neu la version cu
    client_version = None
    if payload.get("json"):
        client_version = payload["json"].get("versionStr") or payload["json"].get("version")

    # Neu client gui version cu "9.9.0", van tra ve success
    # Server KHONG tu dong yeu cau cap nhat nua
    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                # TRA VE VERSION MOI NHAT - client se khong bi bat cap nhat
                "version": "1.0.0103",
                "update_url": "",
                "force": "0",           # 0 = khong bat buoc cap nhat
                "promote_id": "999",
            },
        },
        status=200,
    )


# ============================================================
# ENDPOINT: /sdk/server/get_switch
# CHUC NANG: Tra ve trang thai cac chuc nang (dang ky, dang nhap, thanh toan...)
# ============================================================

@csrf_exempt
def sdk_get_switch(request):
    payload = _collect_request(request)
    print("\n=== /sdk/server/get_switch ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                "reg_switch": "1",
                "login_switch": "1",
                "pay_switch": "0",
                "promote_id": "999",
                "channel_id": "999",
            },
        },
        status=200,
    )


# ============================================================
# ENDPOINT: /sdk/user/equipment_login
# CHUC NANG: Dang nhap thiet bi - BO QUA kiem tra versionStr
# ============================================================

@csrf_exempt
def sdk_equipment_login(request):
    payload = _collect_request(request)
    print("\n=== /sdk/user/equipment_login ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    # LAY THONG TIN TU CLIENT
    client_sign = ""
    client_version = None

    if request.POST:
        first_key = next(iter(request.POST.keys()), "")
        if first_key:
            try:
                decoded = base64.b64decode(first_key, validate=True)
                decoded_text = decoded.decode("utf-8", errors="replace")
                decoded_json = json.loads(decoded_text)
                client_sign = decoded_json.get("md5_sign") or decoded_json.get("t") or ""
                client_version = decoded_json.get("versionStr")

                # LOG version cua client de debug
                if client_version:
                    print(f"[BYPASS] Client gui versionStr: {client_version}")

            except Exception:
                client_sign = ""

    if not client_sign:
        client_sign = "unknown"

    # TAO UID TU CLIENT SIGN
    numeric_uid = "".join([c for c in client_sign if c.isdigit()])
    if not numeric_uid:
        numeric_uid = "10001"

    # TRA VE SUCCESS - KHONG QUAN TAM VERSION
    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                "uid": numeric_uid,
                "username": f"xigu_{numeric_uid}",
                "token": client_sign,
                "is_bind": "1",
            },
        },
        status=200,
    )


# ============================================================
# ENDPOINT: /sdk/user/equipment_down
# CHUC NANG: Dong goi cau hinh thiet bi
# ============================================================

@csrf_exempt
def sdk_equipment_down(request):
    payload = _collect_request(request)
    print("\n=== /sdk/user/equipment_down ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    return JsonResponse(
        {"status": 1, "msg": "success"},
        status=200,
    )


def _verify_account(username, password):
    if not username or not password:
        return None

    account = GameAccount.objects.filter(username=username).first()
    if not account:
        return None

    password_raw = password
    password_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
    if account.password not in (password_raw, password_md5):
        return None

    return account


@csrf_exempt
def sdk_user_login(request):
    payload = _collect_request(request)
    print("\n=== /sdk/user/login ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    username = (request.POST.get("username") or request.POST.get("user") or "").strip()
    password = request.POST.get("password") or request.POST.get("pass") or ""
    account = _verify_account(username, password)

    if not account:
        return JsonResponse({"status": 0, "msg": "invalid_credentials"}, status=200)

    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                "uid": str(account.id),
                "username": account.username,
                "token": "session_success",
            },
        },
        status=200,
    )


@csrf_exempt
def sdk_user_auth(request):
    payload = _collect_request(request)
    print("\n=== /sdk/user/auth ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    username = (request.POST.get("username") or request.POST.get("user") or "").strip()
    password = request.POST.get("password") or request.POST.get("pass") or ""
    account = _verify_account(username, password)

    if not account:
        return JsonResponse({"status": 0, "msg": "invalid_credentials"}, status=200)

    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                "uid": str(account.id),
                "username": account.username,
                "token": "session_success",
            },
        },
        status=200,
    )


@csrf_exempt
def sdk_user_login_account(request):
    payload = _collect_request(request)
    print("\n=== /sdk/user/login_account ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    username = (request.POST.get("username") or request.POST.get("user") or "").strip()
    password = request.POST.get("password") or request.POST.get("pass") or ""
    account = _verify_account(username, password)

    if not account:
        return JsonResponse({"status": 0, "msg": "invalid_credentials"}, status=200)

    return JsonResponse(
        {
            "status": 1,
            "msg": "success",
            "data": {
                "uid": str(account.id),
                "username": account.username,
                "token": "session_success",
            },
        },
        status=200,
    )

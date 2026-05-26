# Bao cao phan tich Moying.dylib

## 1. Tong quan
- File: Moying.dylib
- Dinh dang: Mach-O dylib 64-bit (magic 0xCFFAEDFE)
- Kich thuoc: 129264 bytes
- Thoi gian ghi cuoi: 2026-05-19 15:36:47

## 2. So sanh hai ban
- Doi tuong so sanh:
  - ios/dgame.app/Moying.dylib
  - ios/Payload/dgame.app/Moying.dylib
- SHA256 ca hai ban:
  - DBA54641BB29C71FE41570CC595E5388B4AAB16281515461083F75B39F9A9E40
- Ket luan: Hai ban giong het nhau (hash trung khop, kich thuoc va timestamp trung khop).

## 3. Dau hieu ve chuc nang (tu chuoi va thong diep hook)
Cac chuoi lien quan hook va bao ve:
- "NSMutableURLRequest setAllHTTPHeaderFields: has been hooked!"
- "NSMutableURLRequest setHTTPMethod: has been hooked!"
- "NSMutableURLRequest setURL: has been hooked!"
- "URLSessionDataTaskResumeHooked"
- "+load method has been hooked! Exiting application for security reasons."

Nhan dinh:
- Co co che hook can thiệp vao request (method, header, URL, resume task).
- Co co che phat hien bi hook va tu thoat app de bao ve.

## 4. Lop Objective-C tham chieu
Danh sach lop ObjC duoc tham chieu trong dylib:
- _OBJC_CLASS_$_NSBundle
- _OBJC_CLASS_$_NSDictionary
- _OBJC_CLASS_$_NSJSONSerialization
- _OBJC_CLASS_$_NSMutableURLRequest
- _OBJC_CLASS_$_NSObject
- _OBJC_CLASS_$_NSString
- _OBJC_CLASS_$_NSURL
- _OBJC_CLASS_$_NSURLSession
- _OBJC_CLASS_$_NSURLSessionDataTask
- _OBJC_CLASS_$_Syscall
- _OBJC_CLASS_$_UIAlertAction
- _OBJC_CLASS_$_UIAlertController
- _OBJC_CLASS_$_UIApplication
- _OBJC_CLASS_$_UIDevice
- _OBJC_CLASS_$_UIViewController

Y nghia:
- Mang: NSURLSession, NSMutableURLRequest, NSURL
- JSON: NSJSONSerialization
- UI canh bao: UIAlertController, UIAlertAction
- He thong/app: UIApplication, UIDevice, NSBundle
- Goi he thong: Syscall (co the goi ham he thong truoc khi or sau khi hook)

## 5. Selector/method ObjC trich duoc
Cac selector noi bat:
- dataTaskWithRequest:completionHandler
- setValue:forHTTPHeaderField
- setHTTPMethod
- setHTTPBody
- setURL
- JSONObjectWithData:options:error
- stringWithContentsOfFile:encoding:error
- pathForResource:ofType
- alertControllerWithTitle:message:preferredStyle
- actionWithTitle:style:handler
- presentViewController:animated:completion

Y nghia chinh:
- Tao va gui request, chinh sua method/header/body/url.
- Parse JSON tu response.
- Doc tai nguyen tu bundle.
- Hien thi hop thoai canh bao/chan user.

## 6. URL trich duoc va nhom hanh vi
### 6.1. Endpoint khong phai Apple (nghi la chuc nang chinh)
- https://iosvip555/api/sign/timelock.php
- https://iosvip666/api/sign/timelock.php
- https://iosvip777/api/sign/timelock.php
- https://iosvip888/api/sign/timelock.php
- https://iosvip999/api/sign/timelock.php

Nhan dinh:
- Nhom endpoint timelock kha nang cao la co che kiem tra thoi gian, ky so hoac cap phep (time lock) truoc khi cho phep thuc thi tinh nang nao do.

### 6.2. URL he thong Apple (thuong gap trong chuoi chung chi)
- http://certs.apple.com/wwdrg3.der01
- http://crl.apple.com/root.crl0
- http://ocsp.apple.com/ocsp03-applerootca0.
- http://ocsp.apple.com/ocsp03-wwdrg3010?
- http://www.apple.com/DTDs/PropertyList-1.0.dtd
- https://www.apple.com/appleca/0??
- https://www.apple.com/certificateauthority/0

Luu y:
- Mot so URL co ky tu du thua nhu '.' hoac '?' o cuoi. Day co the la ky tu rac trong binary khi trich chuoi.
- Nhom URL nay thuong lien quan kiem tra chung chi (OCSP/CRL/CA), khong nhat thiet la logic rieng cua app.

## 7. Tong ket hanh vi
- Hook va can thiep request HTTP/HTTPS (method, header, URL, resume task).
- Co co che tu phat hien can thiep (anti-hook) va tu thoat app.
- Co luong goi len endpoint timelock de kiem tra/quyet dinh cho phep.
- Co the hien thi canh bao cho nguoi dung.

## 8. Han che va huong phan tich sau
Han che:
- Phan tich dua tren chuoi/selector, chua disassembly nen chua biet logic chi tiet tung ham.

Goi y buoc tiep:
- Dump Objective-C class/method tu Mach-O (class-dump, otool) tren macOS.
- Disassembly de thay call flow va tham so gui len timelock endpoint.
- Theo doi runtime de xac dinh dieu kien kich hoat canh bao/thoat app.

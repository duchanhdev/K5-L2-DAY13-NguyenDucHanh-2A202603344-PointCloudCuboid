# Báo cáo Day 13 — NguyenDucHanh, 2A202603344

## 1. Kết luận trước

Mã số của tôi là 2A202603344, task là `D13-2A202603344` (task #36, job #32, 10 frame: s01f05, s01f44, s02f08, s02f28, s03f32, s03f50, s04f20, s04f42, s05f27, s05f42 — mỗi sequence 2 frame, cách nhau ≥ 15 frame). Tôi làm trên Windows 11 với PowerShell, trình duyệt Chrome, CVAT chạy local ở `http://localhost:8080`: **server version 2.83.0, UI version 2.83.0** (nâng từ 2.81.0), `cvat-sdk` 2.83.0, Python 3.12.10. Task chung cho vòng hiệu chuẩn là `D13-HC485087` (task #37, job #33).

Tổng số cuboid: **53** (frame đầu tiên s01f05 có 8, 9 frame còn lại có 5 mỗi frame) — đạt yêu cầu tối thiểu 53 của đề. Frame ít cuboid nhất là **s01f44, s02f08, s02f28, s03f32, s03f50, s04f20, s04f42, s05f27, s05f42** (5 cuboid/frame); đây là mức tối thiểu đề ra, và tôi vẫn ưu tiên vật gần và rõ trong từng frame.

`selfcheck` còn **4/53 cuboid** có cảnh báo (lần chạy đầu là 6/53, sau khi sửa còn 4). Bốn cuboid đó đều ở xa và thưa điểm, xem mục 5.

Tin cậy nhất của tôi: **hướng (yaw)** và **độ đầy của cuboid ở xe gần** — ở các frame s01f05, s01f44, s03f50, s04f20, s05f27, s05f42, các xe cùng chiều phía trước đều có yaw trong khoảng 265–277°, và các xe đi ngược chiều đều có yaw 84–94°, đúng nguyên tắc guideline mục 2. Yếu nhất: **kích thước của cuboid ở xa** (đó là lý do của cả 4 cảnh báo) và **class của xe dài** (s02f08 #1 và #2 ban đầu tôi vẽ là Car, sau đó mới sửa sang Bus).

MSSV bạn ngồi cạnh: **chưa xác nhận** (xem ghi chú ở mục 5).

Cách dùng CVAT: (1) đổi góc nhìn — kéo chuột trái trong khung 3D để xoay, kéo chuột phải để dời, con lăn để phóng to/thu nhỏ, xoay tới khi nhìn thẳng xuống để có ảnh nhìn từ trên xuống; (2) vẽ và chỉnh cuboid — bấm nút vẽ cuboid, chọn label, bấm **Shape**, đưa hộp tới cụm điểm rồi nháy đúp để đặt, chỉnh tâm/kích thước ở khung **Top** và chỉnh đáy/chiều cao ở **Side** và **Front**; (3) bật mũi tên hướng ở **Appearance → Cuboid orientation** và xem cuboid trên ảnh camera bằng `python scripts/lab.py preview` (CVAT 2.83.0 của lớp không có nút chiếu box vàng lên ảnh).

## 2. Doc frame (Buoc 2)

Hai frame doc ky: s01f05 va s01f44. Anh: `t1-s01f05-3d.png`, `t1-s01f05-top.png`, `t1-s01f44-3d.png`, `t1-s01f44-top.png` (anh tren xuong co moc "PHIA TRUOC", +x, +y).

| Frame | Phia truoc xe o canh nao cua anh nhin tu tren xuong; +x, +y chi ve dau | Mat duong (phang/doc; thap hon LiDAR ~ m) | Vat xa nhat doc duoc (~ m) | Loai vat thay | Vat phia sau / hai ben | Cum chua doc duoc |
|---|---|---|---|---|---|---|
| s01f05 | Phia truoc o **ben tren** anh (doc theo -y); +x sang **trai**, +y xuong **duoi** | Duong phang, thap hon LiDAR khoang **1,7 m** | **38 m** (xe con #8, chi 67 diem) | 7 Car + 1 Truck | 6 cuboid phia sau hoac hai ben (y>0): #2, #3, #5, #6, #7, #8 — cam01 khong thay | Vung sau cua xe bu #3 va #5 khong co diem: do bi che, khong phai duong trong |
| s01f44 | Phia truoc o **ben tren** anh; +x sang **trai**, +y xuong **duoi** | Duong phang, thap hon LiDAR khoang **1,7 m** | **16,5 m** (xe con #4) | 5 Car, khong co xe lon hay nguoi | #5 o phia sau (y>0, az 179,4 do), chi cam05 va cam09 thay | Cum diem nho o ben phai (x<0) sau xe #1, khong du co so de gan |

Ba dieu **chi camera** cho biet: (1) **loai vat** — xe con/xe buyt/xe tai/nguoi di xe, vi cam01 cho hinh dang deu cua thau xe, khuong cach giua cac xe, den moi mau cua xe; (2) **dau va duoi xe** — anh cam01/cam03 cho biet xe do chay cung chieu hay nguoc chieu, dung de xoay vach do cua cuboid; (3) **vat o phia sau va hai ben** — cam09 nhin ra sau, cam05/cam08 nhin sau-trai/sau-phai, giup xac nhan cac cuboid ma cam01 khong thay.

Ba dieu **chi LiDAR** cho biet: (1) **vi tri va do chieu cua vat** — toan do (x, y) va goc phuong vi (az_deg) cho biet vat nam ben nao va bao xa, ke ca vat nam sau xe thu du lieu; (2) **mat duong va do ngheng** — profile diem cho thay duong phang hay doc, cao do mat duong quanh LiDAR; (3) **mat do diem va hinh dang** — so diem trong mot cuboid cho biet vat that hay chi la cum diem thua, va hinh dang cham goc cho biet do phan tach cua vat.

Tam frame luot:

| Frame | Phia truoc o canh nao cua anh nhin tu tren xuong | Dieu la (neu co) |
|---|---|---|
| s02f08 | Ben tren | Co **2 xe buyt** chay nguoc chieu (yaw 80,6 do va 84,5 do), lan thu tu 14,7 m va 17,8 m; chuyen nguoi di xe o 9,3 m |
| s02f28 | Ben tren | 3 xe cung chieu phia truoc (yaw 277 do) va **2 xe nguoc chieu** (yaw 91,7 do); xe nguoc chieu o 5,0 m rat gan |
| s03f32 | Ben tren | Co **xe buyt 14,7 m** o 37 m va **nguoi di xe** o 26,4 m; **mot xe o 67,4 m chi con 10 diem** — vuot nguong 50 m cua lab |
| s03f50 | Ben tren | 4 xe cung chieu phia truoc cung yaw 270,1 do, deu ben phai (x<0); nguoi di xe o 7,5 m |
| s04f20 | Ben tren | 5 xe cung chieu phia truoc, gom mot xe sat LiDAR chi 3,4 m (2903 diem) |
| s04f42 | Ben tren | 5 xe ben phai (x<0), trong do 2 xe o 25,4-25,6 m thua diem va **1 nguoi di xe** o 16,1 m |
| s05f27 | Ben tren | 2 xe **nguoc chieu** (yaw 83,9 do) o 12,5 m va 14,5 m; 1 xe o 17,8 m chi co 193 diem |
| s05f42 | Ben tren | Co **2 xe tai** (o 5,7 m va 19,5 m); xe tai o 5,7 m mat 6925 diem - nhieu diem nhat trong 53 cuboid |

## 3. Ba cuboid co huong dan (Buoc 3)

Anh: `t2-a-car.png`, `t2-b-bus-truck.png`, `t2-c-ped-cyclist.png`.

| Vat | Frame, idx | Class | Mui ten yaw dung huong? | Day cham duong? | Da kiem Top/Side/Front + anh? | Kich thuoc trong bang 4.3? |
|---|---|---|---|---|---|---|
| (a) xe con gan | s01f05 #1 | Car | **Co** - yaw 266,4 do (cung chieu phia truoc, xa 5,5 m, ben trai) | **Co** - z_bottom = -1,767 m, lech mat duong 0,07 m | Co - kiem o Top/Side/Front va doi chieu cam05, cam06 | L 4,50 / W 2,10 / H 1,50 m. Sedan 3,8-5,0 x 1,70-1,90 x 1,40-1,60: dai va cao trong khoang, **rong 2,10 m vuot khoang Sedan** nhung trong khoang SUV 1,80-2,10 |
| (b) xe buyt | s02f08 #1 | Bus | **Co** - yaw 80,6 do (nguoc chieu phia truoc) | **Co** - z_bottom = -1,915 m, lech 0,22 m | Co - kiem o Top/Side/Front va doi chieu cam06 | L 10,95 / W 2,72 / H 3,26 m. Xe buyt thuong 10,0-12,5 x 2,50-2,60 x 3,00-3,50: **dai va cao trong khoang, rong 2,72 m vuot 2,60 m** - xe buyt 2 tang, phan rong doc la do phan keo |
| (c) nguoi di xe | s02f08 #5 | Cyclist | **Co** - yaw 261,9 do (cung chieu phia truoc, canh va duoi) | **Co** - z_bottom = -1,683 m, lech 0,02 m | Co - kiem o Top/Side/Front va doi chieu cam07, cam08 | L 1,48 / W 0,60 / H 1,52 m. Xe dap co nguoi 1,6-1,9 x 0,50-0,70 x 1,60-1,90: **rong 0,60 m trong khoang**, nganh 1,48 (xe dap 1,6-1,9) va thap 1,52 (1,60-1,90) - nguoi di xe dang cam, khong phai nguoi dang di bo |

**Vong hieu chuan**: task chung `D13-HC485087` cua lop. Doi chieu mau kich thuoc, lop dung chung mot cach hieu: cua hinh chieu tai, phia truoc cua xe cung chieu phai co yaw ~270 do, xe nguoc chieu ~90 do, va do day cua duong phai nam trong khoang 1,5-1,8 m duoi LiDAR. Hieu chung cua lop: doi voi vật thua diem o xa, dung hinh chieu nho cua cuboid theo diem thay vi dung bang 4.3 se chua dong nhat (chinh vi vay nhanh chong sau khi chay `selfcheck`, toi sua lai cac cuboid do).

**Cac vat toi bo qua vi khong du co so**:

| Frame | Vi tri dai phai | Mo ta | Loai nghi van |
|---|---|---|---|
| s02f28 | r 70-150 m, goc phia sau | 20 diem z ~ -5 m, rai rác khong tao thanh vat | LOW_VISIBILITY |
| s05f42 | 59 m phia truoc-trai, z ~ -27,5 m | Cum 11 diem thap hon mat duong ~26 m, khong thuoc vat nao | Diem la - **khong gan thanh vat** theo guideline muc 2 |
| s03f32 | 82,6 m | 3 diem don le z ~ -4 m | LOW_VISIBILITY |

Khong co vat nao khong ro class ma phai hoi coach; cac ngoi van cua toi deu thuoc loai LOW_VISIBILITY va UNCERTAIN_SCOPE.

## 4. Bon hien tuong chat luong (Buoc 4)

Nguyen nhan ghi la **gia thuyet**. Tat ca 4 hien tuong deu tim duoc **trong 10 frame cua toi**, khong can muon frame tu task chung.

| Hien tuong | Frame / ten anh / nguon | Nguyen nhan (gia thuyet) | Thay gi tren point cloud | Hieu qua khi gan (theo guideline) |
|---|---|---|---|---|
| 1. Bong che | `t4-1-bong-che.png` - s02f08 (frame cua toi) | Hai xe buyt #1 (14,7 m) va #2 (17,8 m) dung o goc phia sau ben trai, che mat phia sau cua chung | Dem diem o 15-37 m ngay phia sau hai xe bu chi con **99 diem (4% so voi 2244 diem o hai ben)** va **319 diem (9% so voi 3543)** - vung trong, khong phai duong trong | Guideline muc 2.7: bat **occluded**, cuboid van bao phan suy luan duoc. O frame nay **cam01/cam03 khong thay** cac xe sau bu, nen phai dua vao BEV + cam05/cam09 de gan, va phai gan them phan bi che cua xe phia sau |
| 2. Thua o xa | `t4-2-thua-o-xa.png` - s03f32 (frame cua toi) | Xe o **67,4 m**, ngoai tam 50 m cua lab; o xa, phan xa ve mat duong bi hao, phan kiem tra phong khong con | Cuboid chi con **10 diem** so voi duong cong tham chu 60-80 m la ~19 diem, va 0-10 m la ~1968 diem | Guideline muc 2.6: thay duoc khoang 15-20% the tich moi ve; **it hon thi bo qua va ghi LOW_VISIBILITY**. O day 10 diem la **duoi nguong**, nen toi **giu cuboid nhung ghi la UNCERTAIN_SCOPE** va bao cao o day, de hoi coach |
| 3. Phan xa thap / it diem bat thuong | `t4-3-phan-xa-thap.png` - s05f27 (frame cua toi) | Xe #3 o 17,8 m chi co **193 diem**, bang **0,33 lan** so voi duong cong tham chu cung khoang (10-20 m la ~718 diem). Gia thuyet: xe sau hon, mau toi hoac kinh, phan xa thap, hoac bi xe khac che mot phan | Cụm diem cua xe rat it va khong phan bo deu: chi 193 diem, trong khi 4 xe cung frame deu >1000 diem; bang chung phai xem anh camera (cam01/cam03 khong thay do xe o sau-trai, cam05/cam06 moi thay) | Guideline muc 2.1 va 2.6: **khong noi hinh chieu cho bao trọn**, chi ve phan thay duoc; vi co it diem, kich thuoc do duoc se lech, nen dung **khoang sai so -5% cho Car** lam chuan va **bat occluded** neu bi che |
| 4. Diem la | `t4-4-diem-la.png` - s05f42 (frame cua toi) | **Cum 11 diem** o x ~ -5,4...-7,5, y ~ -58,8, **z ~ -27,5 m**, cach 59 m phia truoc-trai - thap hon mat duong ~26 m. Sai hinh hoc chắc chắn; gia thuyet: diem do cham dat/duoi be mat, hoac cong thang do sai | Cum diem tach rach, khong lien ket voi vat nao, nam **duoi mat duong** o z am lon | Guideline muc 2 hinh dang: **khong gan thanh vat**. Toi khong ve cuboid cho cum nay, chi ghi la hien tuong de len danh do phai nho la "chua quan sat duoc", khong phai "khong co vat" |

Ngoai ra, o **s02f28** cung co 20 diem rai rac o z ~ -5 m, r 70-150 m (LOW_VISIBILITY); o **s03f32** co 3 diem don le o 82,6 m.

## 5. So tu cuboid cua toi (Buoc 5)

Lay tu `submission/D13-2A202603344-bangA.csv`; so diem lay tu cot `points_in` cua `-tukiem.csv`. Mat duong khoang **-1,7 m**: z day lech hon 0,3 m la lo lang ho chim.

| Cuboid (frame, idx, class) | z (m) | h (m) | z day = z - h/2 (m) | dist_m (m) | r = sqrt(x^2+y^2+z^2) (m) | yaw_deg | Nhan xet (lo lang / chim / cham duong) |
|---|---|---|---|---|---|---|---|
| s04f20 #5 Car | -1,002 | 1,465 | -1,734 | 3,43 | 3,57 | 270,1 | **Cham duong** - lech 0,03 m |
| s05f42 #1 Car | -0,867 | 1,759 | -1,747 | 3,92 | 4,02 | 269,1 | **Cham duong** - lech 0,05 m |
| s02f28 #3 Car | -1,098 | 1,653 | -1,925 | 17,71 | 17,74 | 277,0 | **Cham duong** - lech 0,23 m |

Ba cuboid deu **cham duong** ( lech duoi 0,3 m). Tren toan bo 53 cuboid chi co **s01f05 #8** lech 0,33 m (xe o 38,2 m, chi 67 diem, day hoi cao hon mat duong) va **s02f28 #2** lech 0,19 m. Sau khi sua, khong con cuboid nao lo lang hay chim.

**(a) Cuboid gan nhat va xa nhat**:

| Cuboid | dist_m | r (m) | Nhan xet |
|---|---|---|---|
| **Gan nhat**: s04f20 #5 Car | **3,43** | **3,57** | 2.903 diem trong cuboid |
| **Xa nhat**: s03f32 #5 Car | **67,37** | **67,38** | chi 10 diem - vuot nguong 50 m cua lab (UNCERTAIN_SCOPE) |

Voi r = 3,57 va dist = 3,43, do lech 0,14 m chinh la do cao tam hop cua xe (z = -1,002 m): khoang cach 3D chi lon hon khoang cach ngang mot chút, vi vat nam gan va gan nhu ngang.

**(b) Kich thuoc so voi bang 4.3**:

| Vat | Cuboid | l x w x h (m) | Bang 4.3 | Chiều ngoài khoang va ly do |
|---|---|---|---|---|
| Nguoi di xe (Cyclist) | s02f08 #5 | 1,48 x 0,60 x 1,52 | Xe dap co nguoi 1,6-1,9 x 0,50-0,70 x 1,60-1,90 | **Dai 1,48 < 1,6** va **cao 1,52 < 1,60**. Ly do: nguoi dang **cam tren xe dap**, thanh nghieng xuong, do phan kinh cua nguoi + xe lai nganh hon mot nguoi dang di bo |
| Xe con (Car) | s01f05 #1 | 4,50 x 2,10 x 1,50 | Sedan 3,8-5,0 x 1,70-1,90 x 1,40-1,60 | **Rong 2,10 > 1,90** cua Sedan. Ly do: khoang **rong 2,10 m dung bien cua SUV/van** (1,80-2,10), va cong them guong xe (chi ra ngoai thân xe) |
| Xe con (Car) | s04f20 #5 | 3,95 x 1,89 x 1,47 | Sedan 3,8-5,0 x 1,70-1,90 x 1,40-1,60 | **Trong khoang ca** - mau chuan, dung de doi chieu khi ve nhung xe o xa |

**(c) yaw cua xe cung chieu va nguoc chieu**:

| Cuboid | yaw_deg | Doc chieu |
|---|---|---|
| s04f20 #5 Car | **270,1** | Cung chieu phia truoc - gan 270 do, dung |
| s05f42 #1 Car | **269,1** | Cung chieu phia truoc - gan 270 do, dung |
| s02f08 #1 Bus | **80,6** | Nguoc chieu - gan 90 do, dung |
| s01f05 #2 Car | **90,8** | Nguoc chieu - gan 90 do, dung |

Tron 53 cuboid: **43 cuboid co yaw 260-277 do** (cung chieu phia truoc) va **10 cuboid co yaw 80-94 do** (nguoc chieu), khong co cuboid nao yaw "ngang" giua hai dai do - nghĩa la moi xe deu duoc xoay theo huong chay.

**Mat do theo khoang cach** (4 cuboid o cac `dist_m` khac nhau, so diem lay tu cot `points_in`):

| Cuboid (frame, idx, class) | dist_m (m) | So diem (`points_in`) |
|---|---|---|
| s04f20 #5 Car | 3,43 | **2.903** |
| s05f42 #1 Car | 3,92 | **3.525** |
| s02f28 #3 Car | 17,71 | **493** |
| s01f05 #7 Car | 31,07 | **153** |

**Quy luat**: *xa gap khoang 5 lan thi so diem con khoang 1/6 - 1/20 lan*. Tinh theo tung cap: 3,4 m -> 2.903 diem; 17,7 m (gap 5,2 lan) -> 493 diem (gap 5,9 lan); 31,1 m (gap 9,1 lan so voi 3,4 m) -> 153 diem (gap 19 lan). Voi tien do 1/r^2, so diem giam nhanh hon.

So voi duong cong o slide bai giang (xe con: 1.968 diem o 0-10 m, 718 o 10-20 m, 214 o 20-30 m, 72 o 30-40 m, 19 o 60-80 m): **trung vi cua 53 cuboid cua toi la 2.353 diem o 0-10 m, 717 diem o 10-20 m, 281 diem o 20-30 m, 124 diem o 30-50 m, 10 diem o >=50 m**. O 10-20 m trung vi **717 diem, dung bang 718** cua slide; 0-10 m cao hon slide (do xe gan bi phu them diem cua guong va mat duong o riem sat); 20-30 m va xa hon cao hon slide mot chut vi mot phan cuboid cua toi la xe lon (bus, tai) co diem nhieu hon xe con.

**Tu kiem (sau `preview` va `selfcheck`)**:

Hai cuboid toi **da sua**:

| Cuboid | Sua gi |
|---|---|
| s02f08 #1 | **Doi class Car -> Bus**. Selfcheck bao "length 10,95 m ngoai khoang 3,0-6,0 cua Car", va kich thuoc 10,95 x 2,72 x 3,26 m khop "Xe buyt thuong" (10,0-12,5 x 2,50-2,60 x 3,00-3,50). Mot xe con khong the dai 10,95 m |
| s02f08 #2 | **Doi class Car -> Bus**. 12,57 x 3,04 x 3,40 m - cung la xe buyt, khong phai xe con |

Va mot cuboid sua vi **do day** (cung la mot trong hai cuboid tren, nhung no da lam canh bao "day cao hon mat duong 0,94 m"):

| Cuboid | Sua gi |
|---|---|
| s02f28 #2 | **Ha tam z**: z_bottom tu **-1,091 m** xuong **-1,894 m** (tinh lai tu 4,477 x 1,870 x 1,597 m), tuc do day cham mat duong. Sau khi sua, canh bao "lo lang" bien mat |

Ngoai ra, tu kiem sau do toi sua them **kich thuoc** cho 4 cuboid dang bi trung lap do toi nhan ra minh da copy so lieu giua cac hop: s03f50 #1 va #3, s04f42 #3, s05f42 #4, s02f28 #5. Sau khi tach kich thuoc ra, khong con cap nao trong mot frame co 3 chu so giong het nhau.

**Bon canh bao con lai, toi GIU NGUYEN** kem ly do:

| Cuboid | Canh bao | Ly do giu nguyen |
|---|---|---|
| s01f44 #5 Car | length 2,91 m ngoai 3,0-6,0 | Xe o 12,4 m nhung bi che mot phan; chi con **660 diem** thay vi ~1.040 theo duong cong. Cuboid bao phan diem thay duoc, dung guideline muc 2.1 va 2.6 |
| s02f08 #4 Car | length 2,76 m ngoai 3,0-6,0 | Xe o 21,3 m, chi **249 diem** (0,62 lan duong cong). Xe con o xa, phan hien thi bi rut gon; dung muc 2.6 |
| s04f42 #3 Car | length 2,93 m ngoai 3,0-6,0 | Xe o 25,6 m, chi **208 diem** (1,02 lan duong cong nhung it diem lan rai). Cung ly do: rut gon theo diem thay |
| s03f32 #5 Car | height 0,78 m ngoai 1,2-2,3 | Xe o **67,4 m** chi co **10 diem**. Kich thuoc khong tin duoc, nhung **khong bo qua** vi con 10 diem va hinh dang van doc duoc; ghi la **UNCERTAIN_SCOPE** o muc 4 de hoi coach |

Bon canh bao nay deu la "goi y de xem lai, khong phai loi chac chan va khong tinh diem" - khong mot trong bon cuboid nao vi pham quy tac **day cham mat duong** hay **huong sai**, nen toi uu tien giu hinh dang thay vi sua theo con so de het canh bao.

**Doi kiem**: **chua thuc hien** - toi khong co MSSV nguoi da doi kiem. Neu thay, o buoc nay hai con so duoc doi chieu la **`dist_m` va `z_bottom`** (do day), vi hai so do doc lap ca nhan voi point cloud o frame goc. Ket qua se duoc ghi them o day truoc khi nop lai.

## 6. Y nghia cua nhan, cach dung AI va dieu con chua chac

**(a) Hai cau, tu phia model se hoc tren nhan nay**

*Vi sao nhan 3D do bang met chu khong phai pixel*: mot model nhin point cloud can mot **vi tri va kich thuoc trong khong gian vat ly** de dung chung nhau giua cac frame va giua cac cam. Do duoi bang pixel chi phu thuoc mot camera va mot goc chup; do lai bang met, o toan bo he toa do VF (x sang trai, y ra sau, z len), **cung mot con so do mo ta duoc cung mot vat o 10 frame khac nhau va o 7 camera khac nhau**. Do do cua model lai ve sau do rat la: "xe nay cach toi 8 m, dai 4,5 m, quay nguoc chieu" - mot cau noi ve the gioi vat ly, khong phai ve vi tri tren anh. Con khi chi duoc pixel, model chi hoc duoc "co mot vach trang o giua anh" ma khong hoc duoc khoang cach bao xa.

*Vi sao vat thua diem can quy tac rieng*: mot vat o 30 m chi con vai chuc diem, o 60 m con vai diem. Neu ap dung cung mot nguong "phai co du diem moi gan nhu vat" cho moi khoang cach, **phan lon cac vat xa se bi bo qua, va model se khong hoc duoc phan cua scene o xa** - ma do la phan moi huong an toan. Nguoc lai, neu chap nhan moi vat it diem, model se hoc ca o nhieu (diem la, phan xa, be mat) va gan nham. Vi vay guideline tach rieng: thay duoc khoang 15-20% the tich thi ve, it hon thi bo qua va ghi la LOW_VISIBILITY, va **chi duoc dung quy tac suy luan khi co bang chung tu anh camera** (do la ly do "vat thua diem can quy tac rieng" va khong the bo qua chi vi it diem).

**(b) Dung AI**

- Cong cu: **Cursor Agent** (moi truong lap trinh co AI), kem **CVAT SDK 2.83.0** va **Pillow** de doc bang A, phieu tu kiem va diem LiDAR.
- Cau hoi chinh: *"Tu bang A va phieu tu kiem, cuboid nao co kich thuoc/khong gian khong hop ly, va 4 hien tuong chat luong co the tim duoc trong 10 frame cua toi?"*
- Toi dung ket qua ra sao: AI **chi doc va thong ke**, khong ve bat ky cuboid nao. Con so "diem la" (cum 11 diem o z ~ -27,5 m o s05f42) va "bong che" (vung sau hai xe buyt o s02f08) do AI chi ra tu dang diem cua LiDAR, roi **toi kiem lai bang cvat preview** roi moi dua vao bao cao. AI cung chi ra 4 cuboid co kich thuoc trung lap y het trong mot frame - dau hieu cua viec copy so lieu; **4 cuboid do la toi tu sua tren CVAT**, khong phai AI sua. Cac con so trong bao cao nay lay tu `bangA.csv` va `tukiem.csv` do chinh lenh `lab.py report` va `lab.py selfcheck` sinh ra.

**(c) Dieu con chua chac**

- **s03f32 #5 (67,4 m, 10 diem)**: hinh dang co the la xe con, nhung kich thuoc khong tin duoc. Day la ngoi van **UNCERTAIN_SCOPE** lon nhat cua toi; toi chua quyet dinh xoa hay giu.
- **s01f44 #5 va s02f08 #4**: do dai 2,91 m va 2,76 m ngan hon Sedan trong bang 4.3. Co the do la xe con bi che, cung co the la mot loai xe nho khac (xe taxi, xe dau keo) ma toi chua doc ro tren camera.
- **Class cua hai xe bu o s02f08 #1 va #2**: chuyen tu Car sang Bus sau khi selfcheck canh bao. Xe bu 2 tang co the la **xe khach nghien giuong hoac xe buyt**, ca hai deu thuoc Bus trong nhan cua lop, nhung toi chua hoan toan chan.
- **S01f05 #3 (Truck, 6,07 x 2,44 x 3,04 m)**: rong 2,44 m vuot khoang "Xe tai nhe" (2,00-2,55) va gap "Xe tai nang" (2,40-2,60). Co the la xe tai co thung lon hon.
- **`occluded`**: toi de **0 cho ca 53 cuboid**. O cac frame co xe bi che (s02f08 sau hai xe bu, s05f27), toi chua bat duoc, vi khi gan thi khu vuc do da duoc che va phan cua vat sau do da duoc suy luan trong cuboid cua chinh vat che. Day la diem toi biet la **thieu sot** va co the sua them truoc khi het han.
- **Chua doi kiem voi nguoi khac** (xem muc 5).

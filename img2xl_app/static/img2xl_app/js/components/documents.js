// -*- coding: utf-8 -*-

$(document).ready(function () {
	// 1. Khởi tạo bảo mật từ utils.js
	setupCSRF();
	
	// Biến trạng thái toàn cục trong component
	let selectedImageIds = new Set();
	let scale = 1;
	
	// === 1. LOGIC LỌC HÌNH ẢNH ===
	$('.spreadsheet-filter-item, .spreadsheet-filter').on('click', function (e) {
		const id = $(this).data('id').toString();
		
		$('.spreadsheet-filter-item, .spreadsheet-filter').removeClass('active');
		$(this).addClass('active');
		
		if (id === 'all') {
			$('#gallery-header').text('Tất cả hình ảnh');
			$('.gallery-card').fadeIn(200);
		} else {
			const title = $(this).find('.title-text').text();
			$('#gallery-header').text('Ảnh từ: ' + title);
			$('.gallery-card').hide();
			// Sử dụng logic selector của bạn để lọc
			$(`.gallery-card[data-spreadsheet-ids~="${id}"]`).fadeIn(200);
		}
	});
	
	// === 2. SẮP XẾP SIDEBAR (Bảng tính) ===
	$('.btn-sort-sidebar').on('click', function () {
		const type = $(this).data('sort');
		const $list = $('#sidebar-list');
		const items = $list.children('.spreadsheet-filter-item').get();
		
		items.sort(function (a, b) {
			let valA, valB;
			if (type === 'updated') {
				valA = parseInt($(a).attr('data-updated')) || 0;
				valB = parseInt($(b).attr('data-updated')) || 0;
				return valB - valA;
			} else if (type === 'created') {
				valA = parseInt($(a).attr('data-created')) || 0;
				valB = parseInt($(b).attr('data-created')) || 0;
				return valB - valA;
			} else {
				valA = parseInt($(a).attr('data-created')) || 0;
				valB = parseInt($(b).attr('data-created')) || 0;
				return valA - valB;
			}
		});
		
		$.each(items, function (i, li) {
			$list.append(li);
		});
		$('.btn-sort-sidebar').removeClass('btn-secondary text-white').addClass('btn-outline-secondary');
		$(this).removeClass('btn-outline-secondary').addClass('btn-secondary text-white');
	});
	
	// === 3. SẮP XẾP GALLERY (Ảnh) ===
	$('.btn-sort-gallery').on('click', function () {
		const type = $(this).data('sort');
		const $gallery = $('#image-gallery');
		const items = $gallery.children('.gallery-card').get();
		
		items.sort(function (a, b) {
			const tsA = parseInt($(a).data('timestamp'));
			const tsB = parseInt($(b).data('timestamp'));
			return type === 'new' ? tsB - tsA : tsA - tsB;
		});
		
		$.each(items, function (i, card) {
			$gallery.append(card);
		});
		$('.btn-sort-gallery').removeClass('btn-primary').addClass('btn-outline-primary');
		$(this).removeClass('btn-outline-primary').addClass('btn-primary');
	});
	
	// === 4. CHỈNH SỬA TIÊU ĐỀ (Sử dụng Service) ===
	$('.btn-edit-title').on('click', function (e) {
		e.stopPropagation();
		const id = $(this).data('id');
		const oldTitle = $(this).data('title');
		
		Swal.fire({
			title: 'Đổi tên bảng tính',
			input: 'text',
			inputValue: oldTitle,
			showCancelButton: true,
			confirmButtonText: 'Lưu thay đổi',
			cancelButtonText: 'Hủy'
		}).then((result) => {
			if (result.isConfirmed && result.value) {
				// GỌI SERVICE
				apiUpdateTitle(id, result.value).done(function (res) {
					Swal.fire('Đổi tên thành công!', '', 'success').then(() => {
						location.reload();
					});
				});
			}
		});
	});
	
	// === 5. TRÌNH XEM ẢNH ZOOM (UI Logic giữ nguyên) ===
	const overlay = $(`
        <div id="pv-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:9999; cursor:zoom-out; align-items:center; justify-content:center;">
            <div id="pv-container" style="transition: transform 0.1s ease; cursor:default;">
                <img id="pv-img" src="" style="max-width:90vw; max-height:90vh; border-radius:4px; box-shadow:0 0 20px rgba(0,0,0,0.5);">
            </div>
            <div style="position:fixed; bottom:20px; left:50%; transform:translateX(-50%); color:white; background:rgba(0,0,0,0.5); padding:5px 15px; border-radius:20px; pointer-events:none; font-size:12px;">
                Cuộn chuột để Phóng to/Thu nhỏ | Click ra ngoài để đóng
            </div>
        </div>
    `).appendTo('body');
	
	$('.preview-trigger').on('click', function (e) {
		e.stopPropagation();
		const src = $(this).attr('src');
		scale = 1;
		$('#pv-img').attr('src', src);
		$('#pv-container').css('transform', `scale(${scale})`);
		overlay.css('display', 'flex').hide().fadeIn(200);
	});
	
	overlay.on('click', function (e) {
		if (e.target.id === 'pv-overlay' || e.target.id === 'pv-container') {
			overlay.fadeOut(200);
		}
	});
	
	overlay.on('wheel', function (e) {
		e.preventDefault();
		const delta = e.originalEvent.deltaY;
		delta > 0 ? (scale > 0.5 && (scale -= 0.1)) : (scale < 5 && (scale += 0.1));
		$('#pv-container').css('transform', `scale(${scale})`);
	});
	
	// === 6. QUẢN LÝ THÔNG TIN CHI TIẾT ẢNH ===
	$('.tool-img-info').on('click', function (e) {
		e.stopPropagation();
		const container = $(this).closest('.gallery-card');
		const d = container.data();
		
		const sizeFormatted = d.size > 1024 * 1024
			? (d.size / (1024 * 1024)).toFixed(2) + ' MB'
			: (d.size / 1024).toFixed(2) + ' KB';
		
		let deleteText = d.deleteAt && d.deleteAt !== 'None' ? d.deleteAt : 'Không tự động xóa';
		
		Swal.fire({
			title: '<i class="fas fa-edit text-primary"></i> Quản lý hình ảnh',
			html: `
                <div class="text-left border-top pt-3" style="font-size: 14px;">
                    <div class="form-group mb-2">
                        <label class="font-weight-bold">Tên file (Có thể sửa):</label>
                        <input type="text" id="swal-filename" class="form-control form-control-sm" value="${d.filename}">
                    </div>
                    <p class="mb-2"><strong>Dung lượng:</strong> ${sizeFormatted} | <strong>Ngày tải:</strong> ${d.uploaded}</p>
                    <div class="form-group mb-3 p-2 bg-light rounded border">
                        <label class="font-weight-bold text-danger"><i class="fas fa-clock"></i> Tự động xóa:</label>
                        <div class="small mb-1">Hiện tại: <span class="badge badge-warning">${deleteText}</span></div>
                        <select id="swal-duration" class="form-control form-control-sm">
                            <option value="keep">Giữ nguyên hiện tại</option>
                            <option value="0">Không tự động xoá</option>
                            <option value="30">Sau 30 phút</option>
                            <option value="60">Sau 1 giờ</option>
                            <option value="1440">Sau 1 ngày</option>
                        </select>
                    </div>
                    <div class="text-center"><img src="${d.url}" style="max-width: 100%; max-height: 150px; border-radius: 8px;"></div>
                </div>
            `,
			showCancelButton: true,
			confirmButtonText: 'Lưu thay đổi',
			preConfirm: () => {
				const newFilename = document.getElementById('swal-filename').value;
				const newDuration = document.getElementById('swal-duration').value;
				const imgId = container.data('img-id');
				
				if (!newFilename) {
					Swal.showValidationMessage('Tên file không được để trống');
					return false;
				}
				return {id: imgId, filename: newFilename, duration: newDuration};
			}
		}).then((result) => {
			if (result.isConfirmed) {
				// GỌI SERVICE
				apiUpdateImageMetadata(result.value)
					.done(function (response) {
						Swal.fire('Thành công!', 'Thông tin ảnh đã được cập nhật.', 'success')
							.then(() => location.reload());
					})
					.fail(function (xhr) {
						console.error("Lỗi cập nhật:", xhr.responseText);
						Swal.fire('Lỗi!', 'Không thể cập nhật thông tin.', 'error');
					});
			}
		});
	});
	
	// === 7. CHỌN ẢNH & BULK ACTIONS ===
	$('.tool-img-select').on('click', function (e) {
		e.stopPropagation();
		const card = $(this).closest('.gallery-card');
		const imgId = card.data('img-id');
		const icon = $(this).find('.icon-check-img');
		
		if (selectedImageIds.has(imgId)) {
			selectedImageIds.delete(imgId);
			card.removeClass('is-selected');
			icon.removeClass('fa-check-square text-primary').addClass('fa-square');
		} else {
			selectedImageIds.add(imgId);
			card.addClass('is-selected');
			icon.removeClass('fa-square').addClass('fa-check-square text-primary');
		}
		updateImageBulkBar();
	});
	
	function updateImageBulkBar() {
		const count = selectedImageIds.size;
		const $bar = $('#bulk-actions-bar');
		count > 0 ? ($('#selected-count').text(count), $bar.addClass('show')) : $bar.removeClass('show');
	}
	
	$('#btn-cancel-select').on('click', function () {
		selectedImageIds.clear();
		$('.gallery-card').removeClass('is-selected');
		$('.icon-check-img').removeClass('fa-check-square text-primary').addClass('fa-square');
		updateImageBulkBar();
	});
	
	// Xóa đơn lẻ
	$('.tool-img-delete').on('click', function (e) {
		e.stopPropagation();
		const card = $(this).closest('.gallery-card');
		const imgId = card.data('img-id');
		
		Swal.fire({title: 'Xóa ảnh này?', icon: 'warning', showCancelButton: true}).then((result) => {
			if (result.isConfirmed) {
				apiDeleteImage(imgId).done(() => {
					card.fadeOut(300, function () {
						$(this).remove();
					});
					selectedImageIds.delete(imgId);
					updateImageBulkBar();
				});
			}
		});
	});
	
	// Xóa hàng loạt
	$('#btn-bulk-delete').on('click', function () {
		const idsArray = Array.from(selectedImageIds);
		Swal.fire({title: `Xóa ${idsArray.length} ảnh?`, icon: 'error', showCancelButton: true}).then((result) => {
			if (result.isConfirmed) {
				apiBulkDeleteImages(idsArray).done(() => location.reload());
			}
		});
	});
	
	// Cập nhật thời gian hàng loạt
	$('#btn-bulk-edit-time').on('click', function () {
		const idsArray = Array.from(selectedImageIds);
		if (idsArray.length === 0) return;
		
		Swal.fire({
			title: 'Cập nhật thời gian xóa',
			html: `
                <select id="bulk-duration" class="form-control custom-select">
                    <option value="0">Không tự động xoá</option>
                    <option value="30">Sau 30 phút</option>
                    <option value="60">Sau 1 giờ</option>
                    <option value="1440">Sau 1 ngày</option>
                </select>
            `,
			showCancelButton: true,
			preConfirm: () => document.getElementById('bulk-duration').value
		}).then((result) => {
			if (result.isConfirmed) {
				apiBulkUpdateTime(idsArray, result.value).done(() => {
					Swal.fire('Thành công!', '', 'success').then(() => location.reload());
				});
			}
		});
	});
	
	// === 8. XÓA BẢNG TÍNH ===
	$('.btn-delete-res').on('click', function (e) {
		e.stopPropagation();
		const id = $(this).data('id');
		
		Swal.fire({title: 'Xóa bảng tính này?', icon: 'warning', showCancelButton: true}).then((result) => {
			if (result.isConfirmed) {
				// Chú ý: apiDeleteResult chưa có trong service của bạn, tôi viết AJAX tạm thời
				$.post(`/documents/delete-result/${id}/`, function () {
					$(`.spreadsheet-filter-item[data-id="${id}"]`).remove();
					$(`.gallery-card[data-spreadsheet-id="${id}"]`).remove();
					Swal.fire('Đã xóa!', '', 'success');
				});
			}
		});
	});
	
	// === 9. CHI TIẾT TÀI LIỆU ===
	$('.tool-edit').on('click', function (e) {
		e.stopPropagation();
		const d = $(this).closest('.list-item').data();
		Swal.fire({
			title: '<i class="fas fa-file-alt"></i> Chi tiết tài liệu',
			html: `
                <div class="text-left border-top pt-3">
                    <p><strong>Tên:</strong> ${d.filename}</p>
                    <p><strong>ID:</strong> #${d.id}</p>
                    <p><strong>Ngày tạo:</strong> ${d.created}</p>
                    <p><strong>Cập nhật:</strong> ${d.updated}</p>
                    <a href="${d.spreadsheetUrl}" class="btn btn-outline-success btn-block mt-2">Đi tới trang bảng tính</a>
                </div>
            `,
			showCancelButton: true,
			showConfirmButton: false
		});
	});
	
	// === 10. TẠO BẢNG TRỐNG ===
	$('#btn-create-blank').on('click', function () {
		Swal.fire({
			title: 'Đặt tên bảng tính',
			input: 'text',
			showCancelButton: true,
			inputValidator: (v) => !v && 'Bạn cần nhập tên!'
		}).then((result) => {
			if (result.isConfirmed) {
				Swal.showLoading();
				apiCreateBlankSpreadsheet(result.value).done((res) => {
					if (res.status === 'success') window.location.href = res.redirect_url;
				});
			}
		});
	});
});

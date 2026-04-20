// -*- coding: utf-8 -*-
function apiUpdateTitle(id, title) {
	return $.post(`/documents/update-title/${id}/`, {title: title});
}

function apiDeleteImage(id) {
	return $.post(`/documents/delete-image/${id}/`);
}

function apiBulkDeleteImages(ids) {
	return $.ajax({
		url: '/documents/bulk-delete-images/',
		type: 'POST',
		data: JSON.stringify({ids: ids}),
		contentType: 'application/json'
	});
}

function apiCreateBlankSpreadsheet(name) {
	return $.post('/create-spreadsheet-blank/', {name: name});
}

function apiBulkUpdateTime(ids, duration) {
	return $.post('/documents/bulk-update-time/', {'ids[]': ids, 'duration': duration});
}

function apiUpdateImageMetadata(data) {
    return $.post('/documents/update-image-info/', {
        'id': data.id,
        'filename': data.filename,
        'duration': data.duration
    });
}
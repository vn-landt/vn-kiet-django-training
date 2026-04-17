// -*- coding: utf-8 -*-

function saveTableDataAPI(url, data) {
	return fetch(url, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': getCookie('csrftoken')
		},
		body: JSON.stringify({'table_data': data})
	}).then(res => res.json());
}

function generateAIContentAPI(promptText) {
	return fetch('/api/generate-ai-content/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': getCookie('csrftoken')
		},
		body: JSON.stringify({'prompt': promptText})
	}).then(res => res.json());
}
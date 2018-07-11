function login() {
    let accessToken = jQuery('#access-token').val();
    if (accessToken.length == 0)
        jQuery('#empty-token').css('display', 'block');
    else {
        localStorage.setItem('access_token', accessToken);
        window.location.href = '/';
    }
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

function request(method, url, params, callback) {
    jQuery.ajax({
        type: method,
        url: url,
        data: params,
        success: function(data) {
            jQuery('#error-header').css('display', 'none');
            callback(data);
        },
        error: function(data) {
            data = JSON.parse(data['responseText']);
            if (data['error']['error_code'] == 1103)
                logout();
            else {
                jQuery('#error-header').html(data['error']['error_message']);
                jQuery('#error-header').css('display', 'block');
            }
        }
    })
}

function getAccount() {
    let accessToken = localStorage.getItem('access_token');
    request('GET', '/api/account', {access_token: accessToken}, function(data) {
        jQuery('#info-name').html(data['name']);
        jQuery('#info-username').html(`[${data['username']}]`);
    })
}

function getCamera() {
    let accessToken = localStorage.getItem('access_token');
    request('GET', '/api/camera', {access_token: accessToken}, function(data) {
        if (data['camera'].length == 0)
            return;
        sessionStorage.clear();
        for (var i = 0; i < data['camera'].length; ++i) {
            sessionStorage.setItem(`camera_${data['camera'][i]['id']}_name`, data['camera'][i]['name'])
            jQuery('#camera-list').append(`<li id="camera_${data['camera'][i]['id']}" class="nav-item">\n` +
                `            <a href="#" class="nav-link" onclick="clickCamera(${data['camera'][i]['id']})">\n` +
                `              <i class="nav-icon fa fa-video-camera"></i>\n` +
                `              <p>${data['camera'][i]['name']}</p>\n` +
                `            </a>\n` +
                `          </li>`)
        }
        clickCamera(data['camera'][0]['id']);
    })
}

function getStatus(cameraId) {
    let accessToken = localStorage.getItem('access_token');
    request('GET', `/api/camera/${cameraId}/status`, {access_token: accessToken}, function (data) {
        jQuery('#camera-status').prop('checked', data['status']);
    })
}

function postStatus() {
    let accessToken = localStorage.getItem('access_token');
    let cameraId = sessionStorage.getItem('current_camera_id');
    request('POST', `/api/camera/${cameraId}/status`, {
        access_token: accessToken,
        status: jQuery('#camera-status').prop('checked')
    }, function (data) {});
}

function clickCamera(cameraId) {
    jQuery('#content').css('display', 'block');
    if (sessionStorage.getItem('current_camera_id') != null)
        jQuery(`#camera_${sessionStorage.getItem('current_camera_id')} a`).removeClass('active');
    sessionStorage.setItem('current_camera_id', cameraId);
    jQuery(`#camera_${cameraId} a`).addClass('active');
    jQuery('#camera-name-header').html(sessionStorage.getItem(`camera_${cameraId}_name`));
    getStatus(cameraId);
}

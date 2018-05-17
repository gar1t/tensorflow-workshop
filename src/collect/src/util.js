export function fetchData(path, cb) {
  fetch(dataUrl(path)).then(function(resp) {
    return resp.json();
  }).then(function(json) {
    cb(json);
  });
}

export function dataUrl(path) {
  return (
    location.protocol + '//' +
      location.hostname + ':' +
      (process.env.APP_PORT || location.port) +
      path);
}

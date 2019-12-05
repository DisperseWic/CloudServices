#!/usr/bin/python

import argparse
import requests
import os, sys, json, re

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', "--dir",  action='store', help='path to directory with images')
    parser.add_argument('-p', "--path", action='store', help='path to image')
    parser.add_argument('-u', "--url",  action='store', help='url to send', required=True)
    parser.add_argument('-v', "--verbose", action='store_true', help='show request/response')
    parser.add_argument('-t', "--timeout", action='store', type=int, help='request timeout', default=10)
    parser.add_argument("--meta", action='store', help="json with params, e.g.  --meta '{\"space\":\"1\", \"images\":[{\"name\": \"1\"}]}'")

    return parser.parse_args()

def send(url, data, headers, timeout, files = None):
    timeout = timeout or 60
    try:
        r = requests.post(url, data=data, headers=headers, files=files, timeout=timeout)
    except requests.Timeout:
        print('[ERROR] request failed: timed out [timeout: {}, url: {}]'.format(timeout, url))
        return 500, ""

    err_body = ''
    try:
        err_body = r.json()
    except:
        err_body = r.text

    if r.status_code == 200:
        print('[SUCCESS] request status code: {} [url: {}]'.format(r.status_code, url))
    elif r.status_code >= 400 and r.status_code < 500:
        print('[CLIENT_ERROR] request failed, status code: {}, response body: {} [url: {}]'.format(r.status_code, err_body, url))
    else:
        print('[ERROR] request failed, status code: {}, response body: {} [url: {}]'.format(r.status_code, err_body, url))

    return r.status_code, r.text

def build_meta(args, opts, img):
    meta_data = {}

    # allow to append values from console, if there are present in args.images
    if "images" in args:
        for i in range(0, len(img)):
            try:
                extended_img_args = args["images"][i]
            except:
                continue
            for key in extended_img_args:
                img[i][key] = extended_img_args[key]

    if img is not None:
        meta_data['images'] = img

    for key in args:
        if key == "images":
            continue
        if args[key] is None:
            continue
        meta_data[key] = args[key]

    meta = json.dumps(meta_data)
    if opts.get('verbose'):
        print("Request meta: {}".format(meta));
    return meta

def send_images_impl(url, args, opts, img, files, timeout):
    return send(url, {'meta' : build_meta(args, opts, img)}, {}, timeout, files)

def send_images(url, args, opts, fnames, timeout):
    fds = [open(f, 'rb') for f in fnames]

    img = []
    files = {}
    for i in range(0, len(fds)):
        name = 'file_' + str(i)
        img.append({'name' : name})
        files[name] = fds[i]

    return send_images_impl(url, args, opts, img, files, timeout)

def send_images_from_dir(url, args, opts, directory, timeout):
    fnames = [os.path.join(directory, f) for f in os.listdir(directory)]
    return send_images(url, args, opts, fnames, timeout)

def send_args_via_post(url, args, opts, timeout):
    # fake file, it won't be used. it needs to construct correct multipart/form-data request
    files = {'file': ('face.jpg', 'fake data')}
    return send(url, {'meta': build_meta(args, opts, args.get("images"))}, {}, timeout, files)

def string_to_json(args):
    if args == None or len(args) == 0:
        args = "{}"
    meta = json.loads(args)
    return meta

def opts_from_args(args):
    opts = {}
    if args.verbose:
        opts['verbose'] = True
    return opts

if __name__ == "__main__":
    args = parse_arguments()
    meta = string_to_json(args.meta)
    opts = opts_from_args(args)

    if args.path:
        print("Sending image: {}".format(args.path))
        status_code, body = send_images(args.url, meta, opts, [args.path], args.timeout)
    elif args.dir:
        print("Sending images from directory: {}".format(args.dir))
        status_code, body = send_images_from_dir(args.url, meta, opts, args.dir, args.timeout)
    elif re.search("/.*persons/delete\?.*", args.url):
        status_code, body = send_args_via_post(args.url, meta, opts, args.timeout)
    else:
        print("Need path to image or dir")
        sys.exit(1)

    if opts.get('verbose'):
        print("Response body: {}".format(body.encode('utf-8')));

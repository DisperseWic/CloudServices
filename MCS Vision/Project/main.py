from PIL import Image, ImageDraw, ImageFont
import json
import requests
import os
from collections import namedtuple
import uuid
from flask import render_template, redirect, request, send_from_directory
from flask import Flask
from werkzeug.utils import secure_filename

BASE_URL = "https://smarty.mail.ru/api/v1/persons/{}?oauth_provider=mcs&oauth_token={}"

app = Flask(
    __name__,
    static_url_path='',
    static_folder='web/static',
    template_folder='web/templates'
)
app.debug = True

StoredPerson = namedtuple(
    "StoredPerson",
    [
        "uuid",
        "id",
        "img_path"
    ]
)


class Configs:
    token = '2QNB494hUtPjEnL5Yw8Ru8hroCFk6A51R5gAh226jKYmrfJgDu'
    space_id = 1
    base_image = None
    selected_image = None


class Recognizer:
    stored_persons = []
    free_person_id = 1
    configs = Configs()

    @staticmethod
    @app.route("/change_configs")
    def open_change_configs_form():
        return render_template(
            "change_configs_form.html",
            configs=Recognizer.configs
        )

    @staticmethod
    @app.route("/save_configs", methods=["POST"])
    def save_configs():
        Recognizer.configs.token = request.form["token"]
        Recognizer.configs.space_id = int(request.form["space_id"])
        return redirect("/")

    @staticmethod
    @app.route("/")
    def index():
        return render_template(
            "index.html",
            configs=Recognizer.configs,
            stored_persons=Recognizer.stored_persons
        )

    @staticmethod
    @app.route('/img/<imgname>')
    def get_image(imgname):
        return send_from_directory("img", imgname)

    @staticmethod
    @app.route("/remove_person/<uuid>")
    def remove_person(uuid):
        for i in range(len(Recognizer.stored_persons)):
            if Recognizer.stored_persons[i].uuid == uuid:
                url = BASE_URL.format("delete", Recognizer.configs.token)
                response = requests.post(
                    url,
                    data={
                        "meta": json.dumps({
                            "space": str(Recognizer.configs.space_id),
                            "images": [{
                                "name": "myname",
                                "person_id": Recognizer.stored_persons[i].id
                            }]
                        })
                    },
                    files={
                        'file': ("fake_img.jpg", 'fake data')
                    }
                )
                if response.status_code == 200:
                    del Recognizer.stored_persons[i]
                    return redirect("/")

                return render_template(
                    "msg.html",
                    code=str(response.status_code),
                    msg=str(response.text),
                    back_url="/"
                )

    @staticmethod
    @app.route('/select_image')
    def select_image():
        return render_template(
            "select_image_form.html",
            target_url="/set_image"
        )

    @staticmethod
    @app.route("/set_image", methods=["POST"])
    def set_image():
        file = request.files['photo']

        if file.filename:
            filename = os.path.join("img", f"{uuid.uuid4()}_{secure_filename(file.filename)}")
            file.save(filename)
            Recognizer.configs.base_image = filename
        else:
            Recognizer.configs.base_image = None
        Recognizer.configs.selected_image = None

        return redirect("/")

    @staticmethod
    @app.route('/select_person')
    def select_person():
        return render_template(
            "select_image_form.html",
            target_url="/add_person"
        )

    @staticmethod
    @app.route("/add_person", methods=["POST"])
    def add_person():
        file = request.files['photo']

        if file.filename:
            person_uuid = str(uuid.uuid4())
            filename = os.path.join("img", f"{person_uuid}_{secure_filename(file.filename)}")
            file.save(filename)

            url = BASE_URL.format("set", Recognizer.configs.token)
            response = requests.post(
                url,
                data={
                    "meta": json.dumps({
                        "space": str(Recognizer.configs.space_id),
                        "images": [{
                            "name": filename,
                            "person_id": Recognizer.free_person_id
                        }]
                    })
                },
                files={filename: open(filename, "rb")},
            )
            if response.status_code == 200:
                new_person = StoredPerson(person_uuid, Recognizer.free_person_id, filename)
                Recognizer.free_person_id += 1
                Recognizer.stored_persons.append(new_person)
                # return redirect("/")

            return render_template(
                "msg.html",
                code=response.status_code,
                msg=response.text,
                back_url="/"
            )

    @staticmethod
    @app.route("/clear_space")
    def clear_space():
        url = BASE_URL.format("truncate", Recognizer.configs.token)
        response = requests.post(
            url,
            data={
                "meta": json.dumps({
                    "space": str(Recognizer.configs.space_id),
                })
            },
            files={
                'file': ("fake_img.jpg", 'fake data')
            }
        )
        if response.status_code == 200:
            Recognizer.stored_persons.clear()
            return redirect("/")

        return render_template(
            "msg.html",
            code=str(response.status_code),
            msg=str(response.text),
            back_url="/"
        )

    @staticmethod
    @app.route("/recognize")
    def recognize():
        Recognizer.configs.selected_image = None
        if Recognizer.configs.base_image is None:
            return redirect("/")

        url = BASE_URL.format("recognize", Recognizer.configs.token)
        response = requests.post(
            url,
            data={
                "meta": json.dumps({
                    "space": str(Recognizer.configs.space_id),
                    "images": [{
                        "name": Recognizer.configs.base_image,
                        "person_id": Recognizer.free_person_id,
                        "create_new": False
                    }]
                })
            },
            files={Recognizer.configs.base_image: open(Recognizer.configs.base_image, "rb")},
        )
        if response.status_code == 200:
            json_response = json.loads(response.text)
            persons = json_response["body"]["objects"][0]["persons"]
            image = Image.open(Recognizer.configs.base_image)
            draw = ImageDraw.Draw(image)
            for person in persons:
                text_x = min(person["coord"][0], person["coord"][2])
                text_y = min(person["coord"][1], person["coord"][3])
                draw.rectangle(person["coord"])
                draw.text(
                    (text_x, text_y),
                    person["tag"],
                    font=ImageFont.truetype("arial", size=14)
                )

            filepath = f"img\\{str(uuid.uuid4())}.jpg"
            image.save(filepath)
            Recognizer.configs.selected_image = filepath
            return redirect("/")

        return render_template(
            "msg.html",
            code=response.status_code,
            msg=response.text,
            back_url="/"
        )


if __name__ == "__main__":
    app.run()

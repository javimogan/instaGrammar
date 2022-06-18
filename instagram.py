#!/usr/bin/env python3
import sys

from instaloader import Instaloader, Profile
import json
import base64

from datetime import datetime


class Insta:
    def __init__(self, _login_name):
        self.file = 'data.txt'
        self.login_name = _login_name
        self.loader = Instaloader(dirname_pattern="download", title_pattern="{target}")
        self.data = self._load_data()
        self._login()

    def _login(self):
        try:
            self.loader.load_session_from_file(self.login_name)
        except FileNotFoundError:
            self.loader.context.log("Session file does not exist yet - Logging in.")
        if not self.loader.context.is_logged_in:
            self.loader.interactive_login(self.login_name)
            self.loader.save_session_to_file()

    def _load_data(self):
        try:
            with open(self.file, encoding='utf8') as json_file:
                data = json.load(json_file)
        except:
            data = []
        return data

    def _save(self):
        with open(self.file, 'w', encoding='utf8') as outfile:
            json.dump(self.data, outfile)

    def download_profile_by_username(self, _username: str, _download_all_data: bool = True) -> Profile:
        _profile = Profile.from_username(self.loader.context, _username)
        self._download_profile(_profile, _download_all_data=_download_all_data)
        return _profile

    def download_profile_by_userid(self, userid: int, _download_all_data: bool = True) -> Profile:
        _profile = Profile.from_id(self.loader.context, userid)
        self._download_profile(_profile, _download_all_data=_download_all_data)
        return _profile

    def _download_profile(self, _profile: Profile, _download_all_data: bool = True):
        _user = {'id': _profile.userid, 'username': _profile.username, 'full_name': _profile.full_name,
                 'biography': _profile.biography, 'is_private': _profile.is_private,
                 'is_verified': _profile.is_verified, 'number_followers': _profile.followers,
                 'number_followed': _profile.followees, 'updated': datetime.today().strftime("%d/%m/%Y")}
        tam = self._show_percentage(_user['username'], 0.0)
        # download pic
        self.loader.download_title_pic(url=_profile.profile_pic_url, target=_profile.username.lower(),
                                       name_suffix="profile_pic", owner_profile=_profile)
        with open('download/' + _profile.username.lower() + '.jpg', mode='rb') as file:
            img = file.read()
        _user['profile_pic_url'] = base64.encodebytes(img).decode('utf-8')

        if _profile.username == self.login_name or (_download_all_data and (not _profile.is_verified and (
                not _profile.is_private or (_profile.is_private and _profile.followed_by_viewer)))):
            _followers = []
            _followed = []

            _percentage = 0.0
            _total_person = _user['number_followed'] + _user['number_followers']
            _count = 0.0
            for f in _profile.get_followers():
                _count += 1
                _percentage = (_count * 100.0) / _total_person
                tam = self._show_percentage(_user['username'], _percentage, tam)
                _followers.append(f.userid)
            for f in _profile.get_followees():
                _count += 1
                _percentage = (_count * 100.0) / _total_person
                tam = self._show_percentage(_user['username'], _percentage, tam)
                _followed.append(f.userid)

            _user['followers'] = _followers
            _user['followed'] = _followed

        if self.user_is_in_db(_user['id']):
            for i in range(0, len(self.data)):
                if self.data[i]['id'] == _user['id']:
                    self.data.pop(i)
                    break
        self._show_percentage(_user['username'], 100.0, tam)
        print("")
        self.data.append(_user)
        self._save()

    def _show_percentage(self, _user, _percentage, flush: int = 0):
        sys.stdout.write("\b"*flush)
        sys.stdout.write("" * flush)
        sys.stdout.write("\b" * flush)
        msg = 'Load ' + _user + '... ' + str(int(_percentage)) + '%'
        sys.stdout.write(msg)
        return len(msg)

    def username_to_userid(self, user):
        _id = None
        if type(user) is str:
            for _d in self.data:
                if user == _d['username']:
                    _id = _d['id']
            if _id is None:
                _id = self.download_profile_by_username(user, _download_all_data=False).userid
        else:
            _id = user
        return _id

    def userid_to_username(self, userid):
        _username = None
        if type(userid) is int:
            for _d in self.data:
                if userid == _d['id']:
                    _username = _d['username']
            if _username is None:
                _username = self.download_profile_by_userid(userid, _download_all_data=False).username
        else:
            _username = userid
        return _username

    def userid_list_to_username(self, _list: list) -> list:
        if type(_list[0]) is int:
            __list = []
            for _item in _list:
                __list.append(self.userid_to_username(_item))
            return __list
        else:
            return _list

    def username_list_to_userid(self, _list: list) -> list:
        if type(_list[0]) is str:
            __list = []
            for _item in _list:
                __list.append(self.username_to_userid(_item))
            return __list
        else:
            return _list

    def user_is_in_db(self, userid: int) -> bool:
        for _d in self.data:
            if userid == _d['id']:
                return True
        return False

    def get_user_db(self, userid: str = None, username: str = None, _full_user: bool = False):
        user = None
        if userid is None:
            userid = self.username_to_userid(username)

        if not self.user_is_in_db(userid):

            self.download_profile_by_userid(userid, _download_all_data=_full_user)

        for _d in self.data:
            if userid == _d['id']:
                user = _d

        if self.user_is_in_db(userid) and _full_user and (
                'followed' in user and len(user['followed']) + len(user['followers']) == 0):
            self.download_profile_by_userid(user['id'], _download_all_data=_full_user)

            for _d in self.data:
                if userid == _d['id']:
                    user = _d
        return user

    def get_followers(self, _username):
        _user = self.get_user_db(username=_username, _full_user=True)
        return _user['followers']

    def get_following(self, _username):
        _user = self.get_user_db(username=_username, _full_user=True)
        return _user['followed']

    def sort(self, users_id: list, sort_by: str = 'followers', asc: bool = True):
        _values = []
        _sort_by = "number_followers"
        if sort_by == "following":
            _sort_by = "number_followed"
        for _i in users_id:
            _values.append(self.get_user_db(userid=_i))

        _values.sort(key=lambda x: x[_sort_by], reverse=not asc)
        _list = []
        for _v in _values:
            _list.append(_v['id'])
        return _list

    def id_list_to_users_list(self, _list: list):
        _values = []
        for _i in _list:
            _values.append(self.get_user_db(userid=_i))
        return _values


# Test
if __name__ == "__main__":
    insta = Insta(_login_name="javimogan")
    insta.download_profile_by_username(_username="pilarllanos1", _download_all_data=True)

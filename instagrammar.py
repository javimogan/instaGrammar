import logging
from instagram import Insta
from lark import Lark, logger, v_args, Transformer

logger.setLevel(logging.DEBUG)

grammar = """
    ?start: functions+
    
    ?functions: instruction
          | "show" "(" instruction ")"                                           -> show
          | "usernames" "(" instruction ")"                                      -> ids_to_usernames
          | NAME "=" instruction                                                 -> assign_var
          
    ?instruction: instruction "+" instruction                                    -> union
               | instruction "-" instruction                                     -> difference
               | "intersection" + "(" + instruction "," instruction ")"                 -> intersection
               | "symmetric_difference" + "(" + instruction "," instruction ")"         -> symmetric_difference
               | "sort" "(" instruction "," SORT_BY "," SORT ")"                    -> sort
               | "(" instruction ")"
               | "followers" "(" USERNAME ")"                                    -> get_followers
               | "following" "(" USERNAME ")"                                    -> get_following
               | NAME                                                            -> get_var
               
               
    SORT_BY: "following"|"followers"
    SORT: "asc"|"desc"
    USERNAME:  /[^(|)]+/
    %import common.CNAME -> NAME
    %import common.WS
    %ignore WS
"""


@v_args(inline=True)  # Affects the signatures of the methods
class InstaTransformer(Transformer):

    def __init__(self):
        self.insta = Insta(_login_name='javimogan')
        self.vars = {}

    def assign_var(self, _name, _list):

        self.vars[_name] = _list
        return _list

    def get_var(self, _name):
        try:
            return self.vars[_name]
        except KeyError:
            raise Exception("Variable not found: %s" % _name)

    def get_followers(self, value):
        return self.insta.get_followers(str(value))

    def get_following(self, value):
        return self.insta.get_following(str(value))

    def union(self, _list_1, _list_2):
        return list(set(_list_1).union(set(_list_2)))

    def difference(self, _list_1, _list_2):
        return list(set(_list_1).difference(set(_list_2)))

    def intersection(self, _list_1, _list_2):
        return list(set(_list_1).intersection(set(_list_2)))

    def symmetric_difference(self, _list_1, _list_2):
        return list(set(_list_1).symmetric_difference(set(_list_2)))

    def sort(self, _list: list, _sort_by, _sort):
        asc = True
        if _sort == 'desc':
            asc = False
        return self.insta.sort(_list, _sort_by, asc)

    def show(self, _list: list):
        return self.insta.id_list_to_users_list(_list)

    def ids_to_usernames(self, _list: list):
        return self.insta.userid_list_to_username(_list)


def main():
    parser = Lark(grammar, parser='lalr', transformer=InstaTransformer())
    while True:
        code = input('> ')
        try:
            resp = parser.parse(code)
            print(code)
        except Exception as e:
            print(e)



def test():
    parser = Lark(grammar, parser='lalr', transformer=InstaTransformer())
    text = """
        show(sort(following(javimogan) - followers(javimogan), followers, asc))
    """
    text = """
            a = followers(username)
            b = following(username)
            c = b - a
            d = sort(c, followers, asc)
            show(d)
        """
    #text = """a=intersection(following(javimogan), following(username))
    #            """
    resp = parser.parse(text).children
    for _r in resp:
        print(_r)

    
    import json
    json.dumps(resp)
    with open('output.json', 'w', encoding='utf8') as outfile:
        json.dump(resp[-1], outfile)
    #print(Insta(_login_name='username').userid_list_to_username(resp))

if __name__ == '__main__':
    test()
    #main()

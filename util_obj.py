class Author:
    username: str
    public_flags: str
    id: str
    discriminator: str
    avatar_decoration: str
    avatar: str
    bot: bool
    
    def __init__(self, author: dict) -> None:
        self.author = author
        self.__set_author_attributes()
        
    def __set_author_attributes(self) -> None:
        for attr in self.__annotations__:
            try:
                self.__setattr__(attr, self.author[attr])
            except KeyError:
                if attr == "bot":
                    self.bot = False

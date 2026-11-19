# Bank of Meep

Hello future meep, if you're reading this you accidentally `rm -rf`'d the ting.

If that's true, I hope you now finally realise to double check destructive commands like that before pressing enter as soon as you finish writing the command.

Anyway, you need to clone this, and then manually add the game files (keyword, rebus images -> `/rebus_images` and the dataset CSV in the format below in `/rebus_dataset.csv`):

| filename | answer |
| -------- | ------ |
| meep.jpg | Something |

Also, you need to add the token to the .env as it uses `dotenv` to import that. Don't upload that to github whatever you do otherwise some script kiddie might take the cake.

I think that's it, apart from setting up the virtual env and installing the modules from `/requirements.txt` but you already know that.
If you don't, though, maybe you're here for a far greater reason - maybe you had a bad accident (god forbid) that wiped away all knowledge on how to install python module requisistes.
If that is the case, well, it's far worse than I thought and I hope it comes back to you soon.

I think that's everything.

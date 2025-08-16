from cat.mad_hatter.decorators import hook
from .rabbit_hole import RabbitHole

@hook
def after_cat_bootstrap(cat):
    # Rabbit Hole Instance
    cat.rabbit_hole = RabbitHole(cat)  # TODOV2: check if it works, I guess not yet
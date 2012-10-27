from models import UnidirectionalAssoc

class ActionableObject(object):
    """Using this class requires you to add action_counters (DictField) field
    to your model class.
    """
    ASSOC_NS = "action"

    def register_action( self, user_id, action, timestamp=None):
        if( UnidirectionalAssoc.create_user_assoc( user_id, self.id, self.__class__.ASSOC_NS, action)):
            counter = self.action_counters.get( action, 0)
            self.action_counters[action] = counter + 1

    def undo_all_actions( self, user_id):
        assoc_type_list = UnidirectionalAssoc.remove_all_assocs( user_id, self.id, self.__class__.ASSOC_NS)
        action_list = []
        for action in assoc_type_list:
            action_list.append( action)
            counter = self.action_counters.get( action, 0)
            if( counter > 0):
                self.action_counters[action] = counter - 1

        return action_list

    def undo_action( self, user_id, action):
        if( UnidirectionalAssoc.remove_user_assoc( user_id, self.id, self.__class__.ASSOC_NS, action)):
            counter = self.action_counters.get( action, 0)
            if( counter > 0):
                self.action_counters[action] = counter - 1

            return True
        else:
            return False

    def user_has_taken_action( self, user_id, action):
        return UnidirectionalAssoc.user_has_assoc( user_id, self.id, self.__class__.ASSOC_NS, action)

    def action_takers( self, action, count=0):
        return UnidirectionalAssoc.get_associated_users( self.id, self.__class__.ASSOC_NS, action, count)

    def get_action_count( self, action):
        return self.action_counters.get( action, 0)

    def get_all_action_takers( self):
        id_list = []
        for assoc in UnidirectionalAssoc.objects( dest_obj_id=self.id, assoc_ns=self.__class__.ASSOC_NS).only("src_obj_id"):
            id_list.append( assoc.src_obj_id)

        return id_list

    @classmethod
    def set_actions_for_user( cls, user_id, obj_list):
        obj_table = {}
        for obj in obj_list:
            obj.user_action_map = {}
            obj_table[ obj.id] = obj

        for assoc in UnidirectionalAssoc.get_user_assocs( user_id, obj_table.keys(), assoc_ns=cls.ASSOC_NS):
            obj = obj_table[ assoc.dest_obj_id]
            obj.user_action_map[ assoc.assoc_type] = 1

    def get_all_actioned_users( self):
        obj_list = list( UnidirectionalAssoc.objects( dest_obj_id=self.id, assoc_ns=self.__class__.ASSOC_NS))
        return [ obj.src_obj_id for obj in obj_list if obj != None]

class Reaction(object):
    def __init__( self, name, count):
        self.name = name
        self.count = count

class ReactableObject( ActionableObject):
    ASSOC_NS = "reaction"

    @property
    def class_name( self):
        return self.__class__.__name__

    @property
    def default_reactions( self):
        return []

    @property
    def user_reactions( self):
        for reaction in self.default_reactions:
            if( not self.action_counters.has_key( reaction)):
                self.action_counters[ reaction] = 0

        l = []
        for key, value in self.action_counters.items():
            if( value == 0 and key not in self.default_reactions):
                continue

            l.append( Reaction( name=key, count=value))

        def reaction_cmp( v1, v2):
            if( v1.count != v2.count):
                return cmp( v1.count, v2.count)
            return cmp( v2.name, v1.name)

        l.sort( cmp=reaction_cmp, reverse=True)

        return l

    def seed_reactions( self, reaction_list):
        for name in reaction_list:
            if( not self.action_counters.has_key( name)):
                self.action_counters[name] = 0

    @classmethod
    def set_user_reaction( self, user_id, obj_list):
        if( not hasattr( obj_list[0], "user_action_map")):
            ReactableObject.set_actions_for_user( user_id, obj_list)

        for obj in obj_list:
            reactions = obj.user_action_map.keys()
            if( reactions):
                obj.user_reaction = reactions[0]

class VoteableObject( ActionableObject):
    ASSOC_NS = "vote"

    def vote( self, user_id):
        self.undo_all_actions( user_id)
        self.register_action( user_id, "voteup")
        self.set_vote_count()

    def un_vote( self, user_id):
        self.undo_action( user_id, "voteup")
        self.set_vote_count()

    def downvote( self, user_id):
        self.undo_all_actions( user_id)
        self.register_action( user_id, "votedown")
        self.set_vote_count()

    def un_downvote( self, user_id):
        self.undo_action( user_id, "votedown")
        self.set_vote_count()

    @classmethod
    def set_user_vote( cls, user_id, obj_list):
        cls.set_actions_for_user( user_id, obj_list)

        for obj in obj_list:
            if( obj.user_action_map.keys()):
                obj.user_vote = obj.user_action_map.keys()[0]
            else:
                obj.user_vote = ""

    def set_vote_count( self):
        self.vote_count = self.action_counters.get("voteup", 0) - self.action_counters.get("votedown", 0)
        self.__class__.objects(id=self.id).update(set__vote_count=self.vote_count)

class Followable( object):
    def add_follower( self, user_id):
        return UnidirectionalAssoc.create_user_assoc( user_id, self.id, "follow", "follow")

    def remove_follower( self, user_id):
        return UnidirectionalAssoc.remove_user_assoc( user_id, self.id, "follow", "follow")

    def get_followers( self):
        return UnidirectionalAssoc.get_associated_users( self.id, "follow", "follow")

#!/usr/bin/env python
from mongoengine import *

import datetime

class UnidirectionalAssoc( Document):
    """Maintains uni-direction assocation between two objects. It's like
    defining a relationship from src_obj to dest_obj. Key members are:
      * src_obj_id: Id of the source object.
      * dest_obj_id: Id of the destination object.
      * assoc_type: Type of association (e.g. like)

    Examples are:
      * User (source) likes (assoc_type) Post (dest)
      * User (source) votes (assoc_type) on Option A of a Poll (dest)
    """
    src_obj_id = ObjectIdField()
    dest_obj_id = ObjectIdField()
    assoc_ns = StringField()
    assoc_type = StringField()
    timestamp = DateTimeField( default=datetime.datetime.utcnow)

    meta = {
            "indexes": [ ("src_obj_id", "dest_obj_id", "assoc_ns", "assoc_type"), ("dest_obj_id", "assoc_ns", "assoc_type")]
    }

    @classmethod
    def create_assoc( cls, src_obj_id, dest_obj_id, assoc_ns, assoc_type, unique=True):
        """Create assocation between two objects. Unique flag indicates whether
        the source & dest can have multiple instances of the same association
        or not. For example, user-likes-post will have unique as True but in a
        poll where a user can vote multiple times and each vote should count
        separate, unique could be False.
        """
        if( unique):
            assoc = cls.objects( src_obj_id=src_obj_id, dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type).first()
            if( assoc):
                return False

        assoc = cls( src_obj_id=src_obj_id, dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type)
        assoc.save()
        return True

    @classmethod
    def remove_assoc( cls, src_obj_id, dest_obj_id, assoc_ns, assoc_type):
        """Remove association between two objects. E.g. when a user unlikes a
        post, the corresponding association is deleted.
        """
        assoc = cls.objects( src_obj_id=src_obj_id, dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type).first()
        if( not assoc):
            return False

        assoc.delete()
        return True

    @classmethod
    def remove_all_assocs( cls, src_obj_id, dest_obj_id, assoc_ns):
        assoc_list = list( cls.objects( src_obj_id=src_obj_id, dest_obj_id=dest_obj_id, assoc_ns=assoc_ns))
        if( not assoc_list):
            return []

        assoc_type_list = []
        for assoc in assoc_list:
            assoc_type_list.append( assoc.assoc_type)
            assoc.delete()

        return assoc_type_list

    @classmethod
    def has_association( cls, src_obj_id, dest_obj_id, assoc_ns, assoc_type):
        """Finds out if the given source & dest objects have the given
        association or not.
        """
        return cls.objects( src_obj_id=src_obj_id, dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type).count()

    @classmethod
    def get_reverse_association_count( cls, dest_obj_id, assoc_ns, assoc_type):
        """Find out how many associations are present for a given dest and
        association type. Used for things like "how many users like this post?".
        Eventually, this aggregate value should be computed and stored in a
        separate model.
        """
        return cls.objects( dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type).count()

    @classmethod
    def get_reverse_associations( cls, dest_obj_id, assoc_ns, assoc_type, count=0):
        """Get all the reverse associations. For example, list of users who
        have liked a post.
        """
        if( not count):
            l = cls.objects( dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type)
        else:
            l = cls.objects( dest_obj_id=dest_obj_id, assoc_ns=assoc_ns, assoc_type=assoc_type)[:count]

        id_list = []
        for item in l:
            id_list.append( item.src_obj_id)

        return id_list


    @classmethod
    def create_user_assoc( cls, user_id, obj_id, assoc_ns, assoc_type):
        """Shortcut for creating assocation between a user and a destination object."""
        return cls.create_assoc( user_id, obj_id, assoc_ns, assoc_type)

    @classmethod
    def remove_user_assoc( cls, user_id, obj_id, assoc_ns, assoc_type):
        """Shortcut for removing assocation between a user and a destination object."""
        return cls.remove_assoc( user_id, obj_id, assoc_ns, assoc_type)

    @classmethod
    def remove_all_user_assoc( cls, user_id, obj_id, assoc_ns):
        """Shortcut for removing all assocations between a user and a destination object."""
        return cls.remove_all_assocs( user_id, obj_id, assoc_ns)

    @classmethod
    def user_has_assoc( cls, user_id, obj_id, assoc_ns, assoc_type):
        """Shortcut for finding assocation between a user and a destination object."""
        return cls.has_association( user_id, obj_id, assoc_ns, assoc_type)

    @classmethod
    def get_associated_user_count( cls, obj_id, assoc_ns, assoc_type):
        """Shortcut for finding count of users who have association with an object."""
        return cls.get_reverse_association_count( obj_id, assoc_ns, assoc_type)

    @classmethod
    def get_associated_users( cls, obj_id, assoc_ns, assoc_type, count=0):
        """Shortcut for finding users who have association with an object."""
        return cls.get_reverse_associations( obj_id, assoc_ns, assoc_type, count)

    @classmethod
    def get_user_assocs( cls, user_id, obj_id_list, assoc_ns):
        """Finding which objects in the given object id list are associated
        with users. This is across all association types. This works in cases
        where a user can take multiple types of actions on an object (like a
        wall post).
        """
        return list( cls.objects( src_obj_id=user_id, dest_obj_id__in=obj_id_list, assoc_ns=assoc_ns))


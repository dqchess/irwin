from collections import namedtuple, Counter
import numpy as np
from pprint import pprint

class PlayerGameActivations(namedtuple('PlayerGameActivations', ['userId', 'engine', 'generalActivations', 'narrowActivations', 'generalIntermediateActivations', 'narrowIntermediateActivations'])):
  @staticmethod
  def fromTensor(userId, engine, predictions):
    return PlayerGameActivations(
      userId = userId,
      engine = engine,
      generalActivations = [int(100*(np.asscalar(p[0][0][0][0]))) for p in predictions],
      narrowActivations = [int(100*(np.asscalar(p[1][0][0][0]))) for p in predictions],
      generalIntermediateActivations=PlayerGameActivations.gameActivationWords([p[2] for p in predictions]),
      narrowIntermediateActivations=PlayerGameActivations.gameActivationWords([p[3] for p in predictions]))

  @staticmethod
  def gameActivationWords(predictions):
    dicts = [{
        'game': str(int(''.join([('1' if np.asscalar(i) > 0.5 else '0') for i in tensors[1][0]]), 2)),
        'positions': [str(int(''.join([('1' if np.asscalar(i) > 0.5 else '0') for i in p]), 2)) for p in tensors[0][0]]
      } for tensors in predictions]
    return {
      'games': dict(Counter([d['game'] for d in dicts])),
      'positions': dict(sum([Counter(d['positions']) for d in dicts], Counter()))
    }

class PlayerGameActivationsBSONHandler:
  @staticmethod
  def reads(bson):
    return PlayerGameActivations(
      userId = bson['_id'], # userId
      engine = bson['engine'],
      generalActivations = bson['generalActivations'],
      narrowActivations = bson['narrowActivations'],
      generalIntermediateActivations = bson.get('generalIntermediateActivations', {'positions': {}, 'games': {}}),
      narrowIntermediateActivations = bson.get('narrowIntermediateActivations', {'positions': {}, 'games': {}}))

  @staticmethod
  def writes(PlayerGameActivations):
    return {
      '_id': PlayerGameActivations.userId,
      'engine': PlayerGameActivations.engine,
      'generalActivations': PlayerGameActivations.generalActivations,
      'narrowActivations': PlayerGameActivations.narrowActivations,
      'generalIntermediateActivations': PlayerGameActivations.generalIntermediateActivations,
      'narrowIntermediateActivations': PlayerGameActivations.narrowIntermediateActivations
    }

class PlayerGameActivationsDB(namedtuple('PlayerGameActivationsDB', ['playerGameActivationsColl'])):
  def byEngine(self, engine):
    return [PlayerGameActivationsBSONHandler.reads(bson) for bson in self.playerGameActivationsColl.find({'engine': engine}) if len(bson['generalActivations']) >= 7]

  def all(self):
    return [PlayerGameActivationsBSONHandler.reads(bson) for bson in self.playerGameActivationsColl.find()]

  def write(self, playerGameActivations):
    self.playerGameActivationsColl.update_one({'_id': playerGameActivations.userId}, {'$set': PlayerGameActivationsBSONHandler.writes(playerGameActivations)}, upsert=True)

  def lazyWriteMany(self, playerGameActivations):
    [self.write(playerGameActivation) for playerGameActivation in playerGameActivations]
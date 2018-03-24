 ###########################################################
#   Mini Web of Bits Virtual Agent using Q-Leaning Policy   #
#                                                           #
#              Developed by Nathan Shepherd                 #
#                                                           #
 ###########################################################
# Source Code: https://github.com/nathanShepherd/Intelligent-Interface

import gym
import universe
import numpy as np

import time
import random
from CustomDQN_March_18 import DQN

def observe_and_take_random_action(obs):
  # obs is raw (768,1024,3) uint8 screen .
  # The browser window indents the origin of MiniWob by 75 pixels from top and
  # 10 pixels from the left. The first 50 pixels along height are the query.
  if obs is None: return []

  text = obs['text']
  if len(text) > 0:
    print('\n\n}{}{}}{}{}{}{}{}{}{}{}{}{}{')
    print(text)
    print('\n\n}{}{}}{}{}{}{}{}{}{}{}{}{}{')

  x = obs['vision']
  crop = np.array(x[75:75+210, 10:10+160, :]) #mwob coordinates crop
  # crop tensor shape --> (210, 160, 3)
  # crop becomes   [(3, x, 2) matrix, 
  #  a tensor:      (3, y, 3) matrix (value 0-255), 
  #                 (3, y, 3) matrix (value 0-255)]
  
 
  xcoord = np.random.randint(0, 160) + 10# add intelligence
  ycoord = np.random.randint(0, 160) + 75 + 50# add intelligence

  click = 1
  action = coord_to_event(xcoord, ycoord, click)
  print("action: ",action)
  
  #return list of vnc events
  return action

''' Waits for three games until game properly initializes '''
''' TODO: Analyze instructions to pick apropriate Agent   '''
def get_obs_space(env):
  observation = env.reset()
  done = False

  while not done:
    #agent takes an action for each observation
    action_n = [observe_and_take_random_action(obs) for obs in observation]
    observation, reward_n, done_n, info = env.step(action_n)
    
    #print("%%%%%\nInfo:", info['n'][0])
    env_id = info['n'][0]['env_status.episode_id']

    if env_id != None and int(env_id) > 2:
      print("Observation space intialized and returning shape as input to model")
      print("\nObservation: ",observation)
      done = True

  x = observation[0]['vision']
  #crop observation window to fit mwob window
  crop = np.array(x[75:75+210, 10:10+160, :])

  return crop.shape


class Mouse():
  def __init__(self, velocity, penalty_increment):
    self.x_min = 10;
    self.x_max = 170
    self.y_min = 125;
    self.y_max = 280

    self.click = 1
    self.velocity = velocity

    self.x = int(170/2)
    self.y = int(280/2)

    self.penalty = 0
    self.delta = penalty_increment

    self.last_move = 0

  def reset(self):
    self.x = int(170/2)
    self.y = int(280/2)
    self.penalty = 0

  def get_penalty(self):
    return self.penalty

  def last_action(self):
    return self.last_move

  def random_move(self):
    move = random.randrange(0, action_space)
    self.update(move)
    
    return coord_to_event(self.x, self.y, self.click)

  def update(self, action):
    #move left, right
    if action == 0: self.x -= self.velocity
    if action == 1: self.x += self.velocity

    #move up, down
    if action == 2: self.y += self.velocity
    if action == 3: self.y -= self.velocity

    self.last_move = action
    
    if action == 4:
      self.click = 1
    else:
      self.click = 0

    #check for out of bounds
    if self.x > self.x_max:
      self.penalty += self.delta
      self.x = self.x_max - self.velocity
      
    if self.x <= self.x_min:
      self.penalty += self.delta
      self.x = self.x_min + self.velocity
      
    if self.y > self.y_max:
      self.penalty += self.delta
      self.y = self.y_max - self.velocity

    if self.y <= self.y_min:
      self.penalty += self.delta
      self.y = self.y_min + self.velocity

  

def get_training_data(env, vel):
  mouse = Mouse(velocity=vel,
                penalty_increment=0.1)

  training_data = []
  state = env.reset()
  
  for episode in range(num_random_games):
    p = episode*100/num_random_games
    game_memory = []
    game_score = 0
    mouse.reset()
    
    for frame  in range(goal_steps):
      #agent takes an action for each observation
      #action_n = [observe_and_take_random_action(obs) for obs in state]
      action = [mouse.random_move() for obs in state]

      #all transition variables are at least vectors
      state_next, reward, done, info = env.step(action)
      
      print('=========\nObserving random samples: {}%========='.format(p))
      print("\n\n~~~~~~~~ Reward: ", reward,)
      print(    "~~~~~~~~ Action: ", action,)
      print(    "~~~~~~~~   Info: ",   info, "\n\n~~~~~~~~")      

      transition = [state, mouse.last_action(), reward, state_next, done]
      game_memory.append(transition)
      
      game_score += reward[0] - mouse.get_penalty()


      state = state_next
      ##IS THIS LOOP EVER GOING TO END???
      # TODO: end this loop, observe done_n vector
      # Me to me: This loop ends
      
      env.render()
      if done[0]: break

    if game_score > score_requirement:
      #TODO: Restore correlation of entire episode
      # i.e. --> training_data.append(game_memory)
      [training_data.append(trans) for trans in game_memory]

  accepted_scores = [datum[2] for datum in game_memory]
  #for game in training_data:
  #  for trans in game:
  #    accepted_scores.append(trans[2])
  print('Average accepted score:',np.mean(accepted_scores))
  print('Median score for accepted scores:',np.median(accepted_scores))
  print("Number of acccepted scores:", len(accepted_scores))

  #np.save('mwob_Agent_training_data.npy', np.array(training_data))
  return training_data
  


def get_CustomDQN_Agent(env, action_shape, observation_space):
  print('\n\n}{}{}}{}{}{}{}{}{}{}{}{}{}{')
  #print(env.action_space.keys)# get all possible key events
  #print(env.action_space.buttonmasks)# get "buttonmasks"???
  # checkout universe/universe/spaces/vnc_action_space.py
  # ^^^This repo provides more information about key events


'''Take in coordinates on the screen, return action as a list of VNC events'''
def coord_to_event(x, y, click):
  # Line 1: Move to x, y
  # Line 2 & 3: Click at (x, y)
  # TODO: make actions modular with respect to the task required
  #       consider using the env name to decide which class of
  #       set of actions would make the most sense for the context
  action = [universe.spaces.PointerEvent(x, y, 0),
            universe.spaces.PointerEvent(x, y, click),
            universe.spaces.PointerEvent(x, y, 0)]
  return action

def random_game_loop(env):
  observation = env.reset()

  start_time = time.time()
  for episode in range(10):
    for frame  in range(100):
      #agent takes an action for each observation
      action_n = [observe_and_take_random_action(obs) for obs in observation]
      observation, reward_n, done_n, info = env.step(action_n)
      print('####\nReward:', reward_n,'\n')
      print("####\nInfo:", info, '\n')
      #env.render()

      if time.time() - start_time > 25:#30
        break

#~~~~~~~~~~~[  MAIN  ]~~~~~~~~~~~#
    
#initialize game environment
env = gym.make('wob.mini.ClickButton-v0')
goal_steps = 100#just barely starts at 100,000
score_requirement = -100#0
num_random_games = 1#1000
num_training_games = 100#>1000

# (left, right, up, down, click) for Click games
action_space = 5
velocity = 50
 
#TODO: feed instructions through vector space model and train LSTM/CNN/NN
  
if __name__ == "__main__":
  # automatically creates a local docker container
  env.configure(remotes=1, fps=5, vnc_driver='go',
              vnc_kwargs={'encoding':'tight', 'compress_level': 0,
                          'fine_quality_level': 100, 'subsample_level': 0})

  random_game_loop(env)
  
  obs_space= get_obs_space(env)


  training_data = get_training_data(env, velocity)

  print("Compiled random game data, Initializing Agent ...")
  
  initial_observation = env.reset()

  Agent = DQN(batch_size=1,#64
              memory_size=50000,
              learning_rate=0.005,
              random_action_decay=0.5,)

  print("Storing training data")
  for datum in training_data:
      s, a, r, s_, done = datum
      Agent.store_transition(s, a, r, s_, done)

  print("%%%%%\nThe observation space is:",obs_space,"\n%%%%%")
  print("%%%%%\nThe action space is: continuous 2D\n%%%%%")
  Agent.init_model(obs_space, action_space)
  Agent.train()



















































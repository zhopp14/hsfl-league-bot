import copy
import re
from datetime import datetime


import disnake
from disnake.ext import commands

from utils.tools import premium_user_check
from utils.config import not_premium_message, Colors, Links

premium_embed_message = "Embed" #f"Consider buying [Bread Winner Premium]({Links.premium_link}). With it, you get:\n- 1 embed **-> 10 embeds**\n- 5 fields **-> 25 fields**\n- Ability to add an url to embeds\n- Ability to add an timestamp to embeds\n- Ability to add an image to embeds"
# can use set_author, can use set_footer


class InputModal(disnake.ui.Modal):
  def __init__(self, name, base_view, text_inputs, old_values = None, method = None, embed_view = None):
    super().__init__(title = f'{name} Modal', timeout = 300.0, components=text_inputs)
    self.name = name
    self.base_view = base_view
    self.text_inputs = text_inputs
    self.old_values = old_values
    self.method = method
    self.embed_view = embed_view

  async def callback(self, inter):
    name = self.name.lower()
      
    content = inter.text_values.get('content_button')
    if content:
      if content == 'None':
        content = None
      return await inter.response.edit_message(content = content)
      self.base_view.content = content

    edit_embed = inter.text_values.get('edit_embed')
    if edit_embed:
      new_values = []
      for text_input in self.text_inputs:
        new = edit_embed.strip()
        if new:
          if hasattr(text_input, 'convert'):
            try:
              new = text_input.convert(new)
            except Exception as error:
              #error.inter = modal.inter
              raise error
          new_values.append(new)
        else:
          new_values.append(None)
      
      if self.old_values == new_values: # embed is the same
        return await inter.response.defer()

      try:
        if self.method:
          kwargs = {
            text_input.key : new
            for text_input, new in zip(self.text_inputs, new_values)
          }
          getattr(self.embed_view.embed, self.method)(**kwargs) # embed.set_author(name=...,url=...)
        else:
          setattr(self.embed_view.embed, name, new_values[0]) # embed.title = ...
          
        await inter.response.edit_message(embeds = self.base_view.embeds)
        self.embed_view.embed_dict = copy.deepcopy(self.embed_view.embed.to_dict())
        
      except Exception as error:
        self.embed = disnake.Embed.from_dict(self.embed_view.embed_dict)
        self.base_view.embeds[self.embed_view.embed_index] = self.embed
        raise error


    # hard code author, and footer crapp
    
    fields = inter.text_values.get('field_name') or inter.text_values.get("field_value") or inter.text_values.get('field_inline') or inter.text_values.get("field_index")
    if fields:
      inline = inter.text_values.get('field_inline', '').strip() == '1'
      index = None
      index_str = inter.text_values.get("field_index", '0').strip()
      if index_str.isnumeric():
          index = int(index_str)
                                  
      embed = disnake.Embed.from_dict(copy.deepcopy(self.embed_view.embed_dict))
      
      kwargs = {
        'name' : inter.text_values.get('field_name'),
        'value' : inter.text_values.get("field_value"),
        'inline' : inline
      }
      if index or index == 0:
        kwargs['index'] = index
        embed.insert_field_at(**kwargs)
      else:
        embed.add_field(**kwargs)
  
      await self.embed_view.update_fields(embed.to_dict())
      self.base_view.embeds[self.embed_view.embed_index] = embed
      
      try:
        await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
      except Exception as error:
        await self.embed_view.update_fields()
        self.base_view.embeds[self.embed_view.embed_index] = self.embed_view.embed
        raise error
  
      self.embed_view.embed = embed
      self.embed_view.embed_dict = copy.deepcopy(embed.to_dict())

    
    import_msg = inter.text_values.get('import_message')
    if import_msg:
      try:
        value = import_msg.split('/')[-3:]
    
        if inter.guild:
          guild_id, channel_id, message_id = map(int, value)
          assert inter.guild.id == guild_id, 'Message is not in the same guild.'
    
          channel = inter.guild.get_channel_or_thread(channel_id)
          if not channel:
            channel = await inter.guild.fetch_channel(channel_id)
            
          message = await channel.fetch_message(message_id)
        else:
          message_id = int(value[-1])
          message = await inter.user.fetch_message(message_id)

        if message.content:
          self.base_view.content = message.content or None
        if message.embeds:
          self.base_view.embeds = [
            disnake.Embed.from_dict(embed.to_dict())
            for embed in message.embeds
          ]
        else: self.base_view.embeds = []

        await self.base_view.views['message'].update_embeds()
        self.base_view.set_items('message')
        await inter.response.edit_message(
          content = self.base_view.content,
          embeds = self.base_view.embeds,
          view = self.base_view
        )
      except Exception as error:
        raise error      

    edit_msg = inter.text_values.get('edit_message')
    if edit_msg:
      try:
        value = edit_msg.split('/')[-3:]
    
        if inter.guild:
          guild_id, channel_id, message_id = map(int, value)
          assert inter.guild.id == guild_id, 'Message is not in the same guild.'

          
          channel = inter.guild.get_channel_or_thread(channel_id)
          if not channel:
            channel = await inter.guild.fetch_channel(channel_id)
            
          assert channel.permissions_for(inter.user).send_messages, 'You need send_messages permission in the message channel.'
  
          message = await channel.fetch_message(message_id)
          
          if not channel.permissions_for(inter.user).administrator:
            # this is a tiny anti-abuse measure
            # e.g. you dont want non-admins to edit a message sent months ago, it would be hard to find
            now = datetime.now(datetime.timezone.utc)
            seconds_elapsed = (now - message.created_at).seconds
            assert seconds_elapsed < 300, 'Non-admins are disallowed from editing messages older than 5 minutes.'
            
          where = channel.mention
        else:
          message_id = int(value[-1])
          message = await inter.user.fetch_message(message_id)
          where = 'our DMs'
          
        await message.edit(content = self.base_view.content, embeds = self.base_view.embeds)
      
      except Exception as error:
        raise error
      
      await inter.response.send_message(
        content = f"Edited message {message.jump_url} ({message_id}) in {where}",
        ephemeral = True
      )
  
  async def on_timeout(self):
    return


class SendView(disnake.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    if not self.base_view.inter.guild:
      self.channel_button.disabled = True

  @disnake.ui.button(label = 'Send to Channel', style = disnake.ButtonStyle.green)
  async def channel_button(self, button, inter):
    placeholder = 'Select the Channel to send to...'
    guild = inter.guild
    options = [
      disnake.SelectOption(
        label = '#{}'.format(channel.name[:99]),
        description = '{} - {}'.format(
          channel.id,
          channel.topic[:75] if channel.topic else '(no description)'
        ),
        value = channel.id
      )
      for channel in sorted(guild.channels, key = lambda x: x.position)
      if isinstance(channel, (disnake.TextChannel, disnake.Thread)) # text channels only
      if channel.permissions_for(inter.user).send_messages # anti-abuse, user needs send msg perms
    ]
    async def callback(inter):
      channel_id = int(self.base_view.get_select_value())
      
      try:
        channel = guild.get_channel(channel_id)
        if not channel:
          channel = await guild.fetch_channel(channel_id)
        await channel.send(content = self.base_view.content, embeds = self.base_view.embeds)
        
      except Exception as error:
        raise error

      await inter.response.send_message(
        content = f'Sent message to {channel.mention}!',
        ephemeral = True
      )
      
    self.base_view.set_select(placeholder, options, callback, 'send')
    self.base_view.set_items('select')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Edit Message', style = disnake.ButtonStyle.green)
  async def message_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = 'Message URL/Link', 
      placeholder = 'e.g. https://discord.com/channels/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX',
      custom_id = "edit_message"
    )
    
    modal = InputModal(name=button.label, base_view=self.base_view, embed_view=self, text_inputs=text_input)
    await inter.response.send_modal(modal)


class EmbedView(disnake.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    
    self.embed = None # the following are changed often
    self.embed_dict = None # used for default values and reverting changes
    self.embed_original = None # for resetting
    self.embed_index = None # index in self.embeds

  async def update_fields(self, embed_dict = None): # ensures field-related buttons are disabled correctly
    embed_dict = embed_dict or self.embed_dict

    pc = await premium_user_check(self.base_view.bot, self.base_view.inter.author)
    if not pc:
      self.url_button.disabled = True
      self.timestamp_button.disabled = True
      self.image_button.disabled = True
    
    if 'fields' in embed_dict and embed_dict['fields']:
      self.remove_field_button.disabled = False
      pc = await premium_user_check(self.base_view.bot, self.base_view.inter.author)
      if pc: max_fields = 25 
      else: max_fields = 5
      if len(embed_dict['fields']) == max_fields: # max fields in embed
        self.add_field_button.disabled = True
      else:
        self.add_field_button.disabled = False
    else:
      self.remove_field_button.disabled = True
      self.add_field_button.disabled = False
    
  async def do(self, button, inter, *text_inputs, method = None):
    name = button.label.lower()

    old_values = []
    for text_input in text_inputs:
      old = self.embed_dict.get(name, None)
      if hasattr(text_input, 'key'):
        if old:
          old = old.get(text_input.key, None)
      text_input.default = old
      old_values.append(old)
    
    modal = InputModal(name=button.label, base_view=self.base_view, text_inputs=text_inputs, old_values=old_values, method=method, embed_view=self)
    await inter.response.send_modal(modal)

  @disnake.ui.button(label = ' ', disabled = True)
  async def what_button(self, inter, button):
    pass # label is edited to say which embed you're editing

  @disnake.ui.button(label = 'Title', style = disnake.ButtonStyle.blurple)
  async def title_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'The title of the embed', 
      required = False,
      value = None if re.match(r"New embed \d+$", self.embed_dict['title']) else self.embed_dict['title'],
      custom_id = 'edit_embed'
    )
    await self.do(button, inter, text_input)

  @disnake.ui.button(label = 'URL', style = disnake.ButtonStyle.blurple)
  async def url_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'The URL of the embed', 
      required = False,
      value = self.embed_dict.get('url', None),
      custom_id = 'edit_embed'
    )
    await self.do(inter, button, text_input)

  
  @disnake.ui.button(label = 'Description', style = disnake.ButtonStyle.blurple)
  async def description_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'The description of the embed', 
      style = disnake.TextInputStyle.long,
      required = False,
      value = None if self.embed_dict['description'] == premium_embed_message else self.embed_dict['description'],
      custom_id = 'edit_embed'
    )
    await self.do(button, inter, text_input)

  @disnake.ui.button(label = 'Timestamp', style = disnake.ButtonStyle.blurple)
  async def timestamp_button(self, button, inter):
    pc = await premium_user_check(self.base_view.bot, self.base_view.inter.author)
    if not pc:
      return await inter.response.send_message(not_premium_message, ephemeral=True)
      
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'A unix timestamp or a number like "1659876635".', 
      required = False,
      value = self.embed_dict.get('timestamp', None),
      custom_id = "edit_embed"
    )
    def convert(x):
      try:
        return datetime.fromtimestamp(int(x))
      except Exception:
        return datetime.strptime(x, '%Y-%m-%dT%H:%M:%S%z') # 1970-01-02T10:12:03+00:00
        
    text_input.convert = convert
    await self.do(button, inter, text_input)
  
  @disnake.ui.button(label = 'Color', style = disnake.ButtonStyle.blurple)
  async def color_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'A hex string like "#ffab12" or a number <= 16777215.', 
      required = False,
      value = self.embed_dict.get('color', None),
      custom_id = 'edit_embed'
    )
    text_input.convert = lambda x: int(x) if x.isnumeric() else int(x.lstrip('#'), base = 16)
    await self.do(button, inter, text_input)

  # does not work
  '''
  @disnake.ui.button(label = 'Author', style = disnake.ButtonStyle.blurple)
  async def author_button(self, button, inter):
    name_input = disnake.ui.TextInput(
      label = 'Author Name', 
      placeholder = 'The name of the author.', 
      required = True,
      custom_id = 'edit_embed'
    )
    name_input.key = 'name'
    url_input = disnake.ui.TextInput(
      label = 'Author URL', 
      placeholder = 'The URL for the author.', 
      required = False,
      custom_id = 'edit_embeds'
    )
    url_input.key = 'url'
    icon_input = disnake.ui.TextInput(
      label = 'Author Icon URL', 
      placeholder = 'The URL for the author icon.', 
      required = False,
      custom_id = 'edit_embedss'
    )
    icon_input.key = 'icon_url'
    text_inputs = [name_input, url_input, icon_input]
    await self.do(button, inter, *text_inputs, method = 'set_author')
  '''


  @disnake.ui.button(label = 'Image', style = disnake.ButtonStyle.blurple)
  async def image_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'The source URL for the image', 
      required = False,
      value = self.embed_dict.get('image', None),
      custom_id = 'edit_embed'
    )
    text_input.key = 'url'
    await self.do(button, inter, text_input, method = 'set_image')
    

  # footer


  @disnake.ui.button(label = 'Add Field', style = disnake.ButtonStyle.blurple)
  async def add_field_button(self, button, inter):
    name_input = disnake.ui.TextInput(
      label = 'Field Name', 
      placeholder = 'The name of the field',
      custom_id = 'field_name'
    )
    value_input = disnake.ui.TextInput(
      label = 'Field Value', 
      placeholder = 'The value of the field',
      style = disnake.TextInputStyle.long,
      custom_id = "field_value"
    )
    inline_input = disnake.ui.TextInput(
      label = 'Field Inline (Optional)', 
      placeholder = 'Type "1" for inline, otherwise not inline',
      required = False,
      custom_id = "field_inline"
    )
    index_input = disnake.ui.TextInput(
      label = 'Field Index (Optional)',
      placeholder = 'Insert before field(n+1), default at the end',
      required = False,
      custom_id = 'field_index'
    )
    text_inputs = [name_input, value_input, inline_input, index_input]
    
    modal = InputModal(name=button.label, base_view=self.base_view, embed_view=self, text_inputs=text_inputs)
    await inter.response.send_modal(modal)

  @disnake.ui.button(label = 'Remove Field', style = disnake.ButtonStyle.blurple)
  async def remove_field_button(self, button, inter):
    placeholder = 'Select the Field to remove...'
    options = [
      disnake.SelectOption(
        label = f'Field {i+1}', 
        description = field['name'][:100],
        value = i
      )
      for i, field in enumerate(self.embed_dict['fields'])
    ]
    options.append(disnake.SelectOption(label="Clear Fields"))
    
    async def callback(inter):
      if self.base_view.get_select_value() == 'Clear Fields':
          self.embed.clear_fields()
          self.embed_dict = copy.deepcopy(self.embed.to_dict())
          await self.update_fields()
          await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
          return
        
      index = int(self.base_view.get_select_value())
      self.embed.remove_field(index)
      self.embed_dict = copy.deepcopy(self.embed.to_dict())
      await self.update_fields()
      self.base_view.set_items('embed')
      await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)

    self.base_view.set_select(placeholder, options, callback, 'embed')
    self.base_view.set_items('select')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Reset', style = disnake.ButtonStyle.red)
  async def reset_button(self, button, inter):
    self.embed = disnake.Embed.from_dict(copy.deepcopy(self.embed_original))
    self.base_view.embeds[self.embed_index] = self.embed
    self.embed_dict = copy.deepcopy(self.embed_original)
    await self.update_fields()
    await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
  
  @disnake.ui.button(label = 'Back', style = disnake.ButtonStyle.blurple)
  async def back_button(self, button, inter):
    self.base_view.set_items('message')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Stop', style = disnake.ButtonStyle.red)
  async def stop_button(self, button, inter):
    await self.base_view.on_timeout()

  
class SelectView(disnake.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view
    self.options_list = [] # list of options in chunks of 25
    self.has_page_buttons = True
    self.page_index = 0
    self.return_to = None # controls where back button goes, set later

  def update_options(self, options):
    n = 25 # max options in a select
    if len(options) > n:
      if not self.has_page_buttons:
        self.add_item(self.left_button)
        self.add_item(self.what_button)
        self.add_item(self.right_button)
        self.has_page_buttons = True

        self.remove_item(self.back_button)
        self.remove_item(self.stop_button)
        self.add_item(self.back_button)
        self.add_item(self.stop_button)
        
      self.options_list = [options[i:i+n] for i in range(0, len(options), n)]
      self.dynamic_select.options = self.options_list[0]
      self.page_index = 0
      
      self.left_button.disabled = True
      self.right_button.disabled = False
      self.what_button.label = 'Page 1/{}'.format(len(self.options_list))  
    else:
      if self.has_page_buttons:
        self.remove_item(self.left_button)
        self.remove_item(self.what_button)
        self.remove_item(self.right_button)
        self.has_page_buttons = False
      self.dynamic_select.options = options
        
  @disnake.ui.string_select(options = [disnake.SelectOption(label = ' ')])
  async def dynamic_select(self, select, inter):
    pass # callback is changed often

  @disnake.ui.button(label = '<')
  async def left_button(self, button, inter):
    self.page_index -= 1
    if self.page_index == 0:
      button.disabled = True
    self.right_button.disabled = False
    self.what_button.label = 'Page {}/{}'.format(self.page_index+1, len(self.options_list))
    self.dynamic_select.options = self.options_list[self.page_index]
    await inter.response.edit_message(view = self.base_view)
    
  @disnake.ui.button(label = 'Page X/Y', disabled = True)
  async def what_button(self, button, inter):
    pass # purely to tell what button page it is
    
  @disnake.ui.button(label = '>')
  async def right_button(self, button, inter):
    self.page_index += 1
    if self.page_index == len(self.options_list)-1:
      button.disabled = True
    self.left_button.disabled = False
    self.what_button.label = 'Page {}/{}'.format(self.page_index+1, len(self.options_list))
    self.dynamic_select.options = self.options_list[self.page_index]
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Back', style = disnake.ButtonStyle.blurple)
  async def back_button(self, button, inter):
    self.base_view.set_items(self.return_to)
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Stop', style = disnake.ButtonStyle.red)
  async def stop_button(self, button, inter):
    await self.base_view.on_timeout(inter)



class MessageView(disnake.ui.View):
  def __init__(self, base_view):
    super().__init__()
    self.base_view = base_view

  async def update_embeds(self): # ensures embed-related buttons are disabled correctly
    if self.base_view.embeds:
      self.edit_embed_button.disabled = False
      self.remove_embed_button.disabled = False
      pc = await premium_user_check(self.base_view.bot, self.base_view.inter.author)
      if pc:
        max_embeds = 10
      else: 
        max_embeds = 1
      if len(self.base_view.embeds) == max_embeds: # max embeds in a message
        self.add_embed_button.disabled = True
      else:
        self.add_embed_button.disabled = False
    else:
      self.edit_embed_button.disabled = True
      self.remove_embed_button.disabled = True
      self.add_embed_button.disabled = False

  @disnake.ui.button(label = 'Content', style = disnake.ButtonStyle.blurple)
  async def content_button(self, button, inter):
    text_input = disnake.ui.TextInput(
      label = button.label, 
      placeholder = 'The actual content of the message',
      style = disnake.TextInputStyle.long,
      value = self.base_view.content,
      required = False,
      custom_id='content_button',
    )
    
    modal = InputModal(name=button.label, base_view=self.base_view, text_inputs=text_input)
    await inter.response.send_modal(modal)

  @disnake.ui.button(label = 'Add Embed', style = disnake.ButtonStyle.blurple)
  async def add_embed_button(self, button, inter):
    embed = disnake.Embed(title = f'New embed {len(self.base_view.embeds)+1}', description=premium_embed_message)
    self.base_view.embeds.append(embed)
    await self.update_embeds()
    try:
      await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
    except ValueError as error:
      error.inter = inter
      self.base_view.embeds.pop()
      await self.update_embeds()
      raise error


  @disnake.ui.button(label = 'Edit Embed', style = disnake.ButtonStyle.blurple, disabled = True)
  async def edit_embed_button(self, button, inter):
    placeholder = 'Select the Embed to edit...'
    options = [
      disnake.SelectOption(
        label = f'Embed {i+1}',
        description = (
          self.base_view.embeds[i].title[:100] 
          if self.base_view.embeds[i].title
          else '(no title)'
        ),
        value = i
      )
      for i in range(len(self.base_view.embeds))
    ]
    async def callback(inter):
      index = int(self.base_view.get_select_value())
      await self.base_view.set_embed(index)
      self.base_view.set_items('embed')
      await inter.response.edit_message(view = self.base_view)
      
    self.base_view.set_select(placeholder, options, callback)
    self.base_view.set_items('select')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Remove Embed', style = disnake.ButtonStyle.blurple)
  async def remove_embed_button(self, button, inter):
    placeholder = 'Select the Embed to remove...'
    options = [
      disnake.SelectOption(
        label = f'Embed {i+1}',
        description = (
          self.base_view.embeds[i].title[:100] 
          if self.base_view.embeds[i].title
          else '(no title)'
        ),
        value = i
      )
      for i in range(len(self.base_view.embeds))
    ]
    options.append(disnake.SelectOption(label="Clear Embeds"))
    
    async def callback(inter):
      if self.base_view.get_select_value() == 'Clear Embeds':
        self.base_view.embeds = []
        await self.update_embeds()
        await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
        return
        
      index = int(self.base_view.get_select_value())
      self.base_view.embeds.pop(index)
      await self.update_embeds()
      self.base_view.set_items('message')
      await inter.response.edit_message(embeds = self.base_view.embeds, view = self.base_view)
      
    self.base_view.set_select(placeholder, options, callback)
    self.base_view.set_items('select')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Reset', style = disnake.ButtonStyle.red)
  async def reset_button(self, button, inter):
    self.base_view.content = self.base_view.original_content
    self.base_view.embeds = []
    await self.update_embeds()
    await inter.response.edit_message(
      content = self.base_view.content, 
      embeds = self.base_view.embeds, 
      view = self.base_view
    )
  
  @disnake.ui.button(label = 'Import Message', style = disnake.ButtonStyle.green)
  async def import_button(self, button, inter):  
    text_input = disnake.ui.TextInput(
      label = 'Message URL/Link', 
      placeholder = 'e.g. https://discord.com/channels/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX/XXXXXXXXXXXXXXXXXX',
      custom_id = "import_message"
    )

    modal = InputModal(name=button.label, base_view=self.base_view, embed_view=self, text_inputs=text_input)
    await inter.response.send_modal(modal)

  @disnake.ui.button(label = 'Send', style = disnake.ButtonStyle.green)
  async def send_button(self, button, inter):
    self.base_view.set_items('send')
    await inter.response.edit_message(view = self.base_view)

  @disnake.ui.button(label = 'Stop', style = disnake.ButtonStyle.red)
  async def stop_button(self, button, inter):
    await self.base_view.on_timeout()


class BaseView(disnake.ui.View):
  def __init__(self, bot, inter):
    super().__init__()
    self.bot = bot
    self.inter = inter
    self.message = None # set later, used for timeout edits
    self.content = 'Embed Builder'
    self.original_content = self.content
    self.embeds = []
    self.views = {
      'message' : MessageView(self),
      'select' : SelectView(self),
      'embed' : EmbedView(self),
      'send' : SendView(self)
    }
    self.set_items('message')

  def set_items(self, key):
    self.clear_items()
    for item in self.views[key].children:
      self.add_item(item)

  def get_select_value(self):
    select = self.views['select'].dynamic_select
    return select.values[0]

  async def set_embed(self, index):
    embed = self.embeds[index]
    view = self.views['embed']
    view.embed = embed
    view.embed_dict = copy.deepcopy(embed.to_dict())
    view.embed_original = disnake.Embed(title = f'New embed {index+1}').to_dict()
    view.embed_index = index
    view.what_button.label = f'*Editing Embed {index+1}'
    await view.update_fields()

  def set_select(self, placeholder, options, callback, return_to = None):
    view = self.views['select']
    view.return_to = return_to or 'message'
    select = view.dynamic_select
    select.placeholder = placeholder
    select.callback = callback
    view.update_options(options)

  async def interaction_check(self, inter):
    if inter.author.id != self.inter.author.id:
      await inter.response.send_message("This is not your menu!", ephemeral=True)
      return False
    return True

  async def on_timeout(self):
    try: # hide buttons
        self.stop()
        await self.inter.edit_original_message(view = None) 
    except disnake.HTTPException: # disable buttons if message is empty
      for item in self.children:
        item.disabled = True
      await self.inter.edit_original_message(view = self)
      
  async def on_error(self, error, item, inter):
    embed = disnake.Embed(
      title = 'Edit failed',
      description = '```fix\n{}```',
      color = Colors.red
    )
    if isinstance(error, disnake.HTTPException):
      embed.description = embed.description.format(error.text)
    elif isinstance(error, (ValueError, TypeError, AssertionError)):
      embed.description = embed.description.format(str(error))
    else:
      # print('unhandled error:', inter, error, item, error.__class__.__mro__, sep = '\n')
      raise error
    embed.description = embed.description or 'No reason provided.'
    if hasattr(error, 'inter'): # use inter if available e.g. .convert() failed
      await inter.response.send_message(embed = embed, ephemeral = True)
    else: # otherwise followup e.g. for max embeds reached
      await self.inter.followup.send(embed = embed, ephemeral = True)

class EmbedCommands2(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.slash_command()
  async def embed(self, inter):
    """desc"""
    await inter.response.defer()
    view = BaseView(self.bot, inter)
    await inter.send(content=view.content, view=view)

def setup(bot):
  bot.add_cog(EmbedCommands2(bot))
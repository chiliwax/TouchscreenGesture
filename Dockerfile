# Use Ubuntu as base image
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    python3 \
    python3-pip \
    python3-evdev \
    python3-dev \
    xdotool \
    x11-apps \
    x11-xserver-utils \
    x11-utils \
    x11vnc \
    xvfb \
    dbus-x11 \
    default-jre \
    xauth \
    x11vnc \
    sudo \
    udev \
    build-essential \
    linux-headers-generic \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# Create a non-root user
RUN useradd -m -s /bin/bash touchgesture
RUN getent group input || groupadd input
RUN usermod -aG input touchgesture
RUN echo "touchgesture ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Set up X11 environment
ENV DISPLAY=:99
ENV XAUTHORITY=/home/touchgesture/.Xauthority

# Create necessary directories and set permissions
RUN mkdir -p /etc/touchgesture \
    && mkdir -p /home/touchgesture/.config/touchgesture \
    && mkdir -p /dev/input \
    && chown -R touchgesture:touchgesture /etc/touchgesture \
    && chown -R touchgesture:touchgesture /home/touchgesture/.config \
    && chmod 666 /dev/input/* || true

# Create and set up start script
COPY start.sh /usr/local/bin/start-touchgesture
RUN chmod +x /usr/local/bin/start-touchgesture

# Copy application files
COPY . /opt/touchgesture/
RUN chown -R touchgesture:touchgesture /opt/touchgesture \
    && chmod +x /opt/touchgesture/touchgesture.py

# Download virtual touchscreen
RUN wget https://github.com/vi/virtual_touchscreen/releases/download/v1.0/virtual_touchscreen.jar -O /opt/touchgesture/virtual_touchscreen.jar \
    && chmod +x /opt/touchgesture/virtual_touchscreen.jar \
    && chown touchgesture:touchgesture /opt/touchgesture/virtual_touchscreen.jar

# Clone and build virtual touchscreen
RUN git clone https://github.com/vi/virtual_touchscreen.git /opt/virtual_touchscreen \
    && cd /opt/virtual_touchscreen \
    && make

# Switch to non-root user
#USER touchgesture
WORKDIR /opt/touchgesture

# Expose VNC port
EXPOSE 5900

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/start-touchgesture"]

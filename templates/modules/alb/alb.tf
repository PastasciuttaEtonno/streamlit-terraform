# 1. Security Group per l'ALB (Aperto al mondo)
resource "aws_security_group" "alb_sg" {
  name        = "${var.environment_name}-alb-sg"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.ingress_port
    to_port     = var.ingress_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. Il Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnet_ids # Sempre nelle pubbliche!

  tags = { Name = "${var.environment_name}-ALB" }
}

# 3. Target Group
resource "aws_lb_target_group" "main" {
  name     = "${var.environment_name}-tg"
  port     = 80 # Porta su cui ascoltano le istanze (es. Nginx)
  protocol = "HTTP"
  vpc_id   = var.vpc_id
  
  health_check {
    path = "/" # Controlla se la home page risponde
  }
}

# 4. Listener
resource "aws_lb_listener" "front_end" {
  load_balancer_arn = aws_lb.main.arn
  port              = var.ingress_port
  protocol          = "HTTP"

  default_action {
    # Il tipo è sempre richiesto
    type = var.listener_action_type

    # Se è "forward", colleghiamo il target group. Altrimenti null.
    target_group_arn = var.listener_action_type == "forward" ? aws_lb_target_group.main.arn : null

    # --- BLOCCO DINAMICO PER REDIRECT ---
    # Viene creato solo se action_type == 'redirect'
    dynamic "redirect" {
      for_each = var.listener_action_type == "redirect" ? [1] : []
      content {
        port        = var.redirect_port
        protocol    = var.redirect_protocol
        status_code = var.redirect_status_code
      }
    }

    # --- BLOCCO DINAMICO PER FIXED RESPONSE ---
    # Viene creato solo se action_type == 'fixed-response'
    dynamic "fixed_response" {
      for_each = var.listener_action_type == "fixed-response" ? [1] : []
      content {
        content_type = var.fixed_response_content_type
        message_body = var.fixed_response_body
        status_code  = var.fixed_response_code
      }
    }
  }
}

# 5. Attachment (Collega le istanze create nel modulo EC2)
resource "aws_lb_target_group_attachment" "main" {
  # Cicla su tutte le istanze che gli passiamo
  count            = length(var.target_instance_ids)
  target_group_arn = aws_lb_target_group.main.arn
  target_id        = var.target_instance_ids[count.index]
  port             = 80
}


